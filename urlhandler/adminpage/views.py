#-*- coding:utf-8 -*-

from datetime import datetime
from django.contrib import auth
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlquote
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
import re
import time
import urllib
import urllib2
import xlwt

from adminpage.safe_reverse import *
from queryhandler.settings import QRCODE_URL
from urlhandler.models import Activity, Ticket, Seat
from urlhandler.models import User as Booker
from weixinlib.custom_menu import get_custom_menu, modify_custom_menu, add_new_custom_menu, auto_clear_old_menus
from weixinlib.settings import get_custom_menu_with_book_acts, WEIXIN_BOOK_HEADER


@csrf_protect
def home(request):
    if not request.user.is_authenticated():
        return render_to_response('login.html', context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(s_reverse_activity_list())


def activity_list(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())

    act_models = Activity.objects.filter(status__gte=0).order_by('-id').all()
    activities = []
    for act in act_models:
        activities += [wrap_activity_dict(act)]
    permission_num = 1 if request.user.is_superuser else 0
    return render_to_response('activity_list.html', {
        'activities': activities,
        'permission': permission_num,
    })


def activity_checkin(request, act_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())
    try:
        activity = Activity.objects.get(id=act_id)
        if datetime.now() > activity.end_time:
            raise 'Time out!'
    except ObjectDoesNotExist:
        return HttpResponseRedirect(s_reverse_activity_list())

    return render_to_response('activity_checkin.html', {
        'activity': activity,
    }, context_instance=RequestContext(request))


def activity_checkin_post(request, act_id):
    if (not request.POST) or (not ('uid' in request.POST)):
        raise Http404
    try:
        activity = Activity.objects.get(id=act_id)
    except ObjectDoesNotExist:
        return HttpResponse(json.dumps({'result': 'error', 'stuid': 'Unknown', 'msg': 'noact'}),
                            content_type='application/json')

    return_json = {'result': 'error', 'stuid': 'Unknown', 'msg': 'rejected'}
    flag = False
    uid = request.POST['uid']
    if len(uid) == 10:
        if not uid.isdigit():
            return_json['result'] = 'error'
            return_json['stuid'] = 'Unknown'
            return_json['msg'] = 'rejected'
            flag = True
        if not flag:
            return_json['stuid'] = uid
            try:
                student = Booker.objects.get(stuid=uid, status=1)
            except ObjectDoesNotExist:
                return_json['msg'] = 'nouser'
                flag = True
            if not flag:
                try:
                    ticket = Ticket.objects.get(stuid=student.stuid, activity=activity)
                    if ticket.status == 0:
                        raise 'noticket'
                    elif ticket.status == 2:
                        return_json['result'] = 'warning'
                        return_json['msg'] = 'used'
                    elif ticket.status == 1:
                        ticket.status = 2
                        ticket.save()
                        return_json['msg'] = 'accepted'
                        return_json['result'] = 'success'
                except ObjectDoesNotExist:
                    return_json['msg'] = 'noticket'
    elif len(uid) == 32:
        try:
            ticket = Ticket.objects.get(unique_id=uid, activity=activity)
            if ticket.status == 0:
                raise 'rejected'
            elif ticket.status == 2:
                return_json['msg'] = 'used'
                return_json['stuid'] = ticket.stuid
                return_json['result'] = 'warning'
            else:
                ticket.status = 2
                ticket.save()
                return_json['result'] = 'success'
                return_json['stuid'] = ticket.stuid
                return_json['msg'] = 'accepted'
        except ObjectDoesNotExist:
            return_json['result'] = 'error'
            return_json['stuid'] = 'Unknown'
            return_json['msg'] = 'rejected'

    return HttpResponse(json.dumps(return_json), content_type='application/json')


def login(request):
    if not request.POST:
        raise Http404

    return_json = {}
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')

    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)
        return_json['message'] = 'success'
        return_json['next'] = s_reverse_activity_list()
    else:
        time.sleep(2)
        return_json['message'] = 'failed'
        if User.objects.filter(username=username, is_active=True):
            return_json['error'] = 'wrong'
        else:
            return_json['error'] = 'none'

    return HttpResponse(json.dumps(return_json), content_type='application/json')


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(s_reverse_admin_home())


def str_to_datetime(strg):
    return datetime.strptime(strg, '%Y-%m-%d %H:%M:%S')


def activity_create(activity):
    act_dict = dict()
    for k in ['name', 'key', 'description', 'place', 'pic_url', 'seat_status', 'total_tickets']:
        act_dict[k] = activity[k]
    for k in ['start_time', 'end_time', 'book_start', 'book_end']:
        act_dict[k] = str_to_datetime(activity[k])
    act_dict['status'] = 1 if ('publish' in activity) else 0
    act_dict['remain_tickets'] = act_dict['total_tickets']
    act_dict['seat_table'] = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                              [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                              [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                              [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
    new_act = Activity.objects.create(**act_dict)
    return new_act


def seat_create(post, activity):
    seats = Seat.objects.filter(activity=activity)
    if seats.exists():
        seats.delete()
    seat_dict = dict()
    print post['seat_status']
    if post['seat_status'] == '1':
        for k in ['zongtiA', 'zongtiB', 'zongtiC', 'zongtiD', 'zongtiE']:
            for i in range(int(post[k])):
                seat_dict['position_row'] = 0
                seat_dict['position_column'] = 0
                seat_dict['seat_section'] = k[-1]
                seat_dict['price'] = 0
                seat_dict['is_selected'] = 0
                seat_dict['activity'] = activity
                new_seat = Seat.objects.create(**seat_dict)
    elif post['seat_status'] == '2':
        for row in range(1, 5):
            for column in range(1, 11):
                print row
                print column
                seat_dict['position_row'] = row
                seat_dict['position_column'] = column
                seat_dict['seat_section'] = ''
                seat_dict['price'] = 0
                seat_dict['is_selected'] = 0
                seat_dict['activity'] = activity
                new_seat = Seat.objects.create(**seat_dict)


def activity_modify(activity):
    now_act = Activity.objects.get(id=activity['id'])
    now = datetime.now()
    if now_act.status == 0:
        key_list = ['name', 'key', 'description', 'place', 'pic_url', 'seat_status', 'total_tickets']
        time_list = ['start_time', 'end_time', 'book_start', 'book_end']
        seat_create(activity, now_act)
    elif now_act.status == 1:
        if now >= now_act.start_time:
            key_list = ['description', 'pic_url']
            time_list = ['start_time', 'end_time']
        elif now >= now_act.book_start:
            key_list = ['description', 'place', 'pic_url']
            time_list = ['start_time', 'end_time', 'book_end']
        else:
            key_list = ['description', 'place', 'pic_url', 'seat_status', 'total_tickets']
            time_list = ['start_time', 'end_time', 'book_end']
            seat_create(activity, now_act)
    else:
        key_list = []
        time_list = []
    for key in key_list:
        if key == 'total_tickets':
            setattr(now_act, 'remain_tickets', activity[key])
        setattr(now_act, key, activity[key])
    for key in time_list:
        setattr(now_act, key, str_to_datetime(activity[key]))
    if (now_act.status == 0) and ('publish' in activity):
        now_act.status = 1
    now_act.save()
    return now_act


@csrf_exempt
def activity_delete(request):
    request_data = request.POST
    if not request_data:
        raise Http404
    current_act = Activity.objects.get(id=request_data.get('activityId', ''))
    current_act.status = -1
    current_act.save()
    # 删除后刷新界面
    return HttpResponse('OK')


def get_checked_tickets(activity):
    return Ticket.objects.filter(activity=activity, status=2).count()


def wrap_activity_dict(activity):
    dt = model_to_dict(activity)
    if (dt['status'] >= 1) and (datetime.now() >= dt['book_start']):
        dt['tickets_ready'] = 1
        dt['ordered_tickets'] = int(activity.total_tickets) - int(activity.remain_tickets)
        dt['checked_tickets'] = get_checked_tickets(activity)
    return dt


def activity_add(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())

    return render_to_response('activity_detail.html', {
        'activity': {
            'name': u'新建活动',
        },
        'seats_list': [[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                       [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                       [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                       [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                       [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0],
                       [0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0],
                       [0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0],
                       [0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0],
                       [0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0],
                       [0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0],
                       [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 0],
                       [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 0],
                       [0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0],
                       [0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0]],
        'chosen_seats': []
    }, context_instance=RequestContext(request))


def activity_detail(request, act_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())

    try:
        activity = Activity.objects.get(id=act_id)
        unpublished = (activity.status == 0)
    except:
        raise Http404
    return render_to_response('activity_detail.html', {
        'activity': wrap_activity_dict(activity),
        'unpublished': unpublished,
        'seats_list': [[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                       [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                       [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                       [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                       [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0],
                       [0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0],
                       [0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0],
                       [0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0],
                       [0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0],
                       [0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0],
                       [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 0],
                       [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 0],
                       [0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0]]
    }, context_instance=RequestContext(request))


class DatetimeJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)


def activity_post(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())

    if not request.POST:
        raise Http404
    post = request.POST
    return_json = dict()
    try:
        if 'id' in post:
            activity = activity_modify(post)
        else:
            is_key = Activity.objects.filter(key=post['key'])
            if is_key:
                now = datetime.now()
                for key_act in is_key:
                    if now < key_act.end_time:
                        return_json['error'] = u"当前有活动正在使用该活动代称"
                        return HttpResponse(json.dumps(return_json, cls=DatetimeJsonEncoder),
                                            content_type='application/json')
            activity = activity_create(post)
            seat_create(post, activity)
            return_json['updateUrl'] = s_reverse_activity_detail(activity.id)
        return_json['activity'] = wrap_activity_dict(activity)
        if 'publish' in post:
            update_error = json.loads(add_new_custom_menu(
                name=activity.key, key=WEIXIN_BOOK_HEADER + str(activity.id))).get('errcode', 'err')
            if update_error != 0:
                return_json['error'] = u'活动创建成功，但更新微信菜单失败，请手动更新:(  \r\n错误代码：%s' % update_error
    except Exception as e:
        return_json['error'] = str(e)
    return HttpResponse(json.dumps(return_json, cls=DatetimeJsonEncoder), content_type='application/json')


def order_index(request):
    return render_to_response('print_login.html', context_instance=RequestContext(request))


def order_login(request):
    if not request.POST:
        raise Http404

    return_json = {}
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')

    try:
        Booker.objects.get(stuid=username)
    except ObjectDoesNotExist:
        return_json['message'] = 'none'
        return HttpResponse(json.dumps(return_json), content_type='application/json')

    req_data = urllib.urlencode({'userid': username, 'userpass': password, 'submit1': u'登录'.encode('gb2312')})
    request_url = 'https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp'
    req = urllib2.Request(url=request_url, data=req_data)
    res_data = urllib2.urlopen(req)

    try:
        res = res_data.read()
    except:
        raise Http404

    if 'loginteacher_action.jsp' in res:
        request.session['stuid'] = username
        request.session.set_expiry(0)
        return_json['message'] = 'success'
        return_json['next'] = s_reverse_order_list()
    else:
        return_json['message'] = 'failed'

    return HttpResponse(json.dumps(return_json), content_type='application/json')


def order_logout(request):
    return HttpResponseRedirect(s_reverse_order_index())


def order_list(request):

    if not ('stuid' in request.session):
        return HttpResponseRedirect(s_reverse_order_index())

    student_id = request.session['stuid']

    orders = []
    queryset = Ticket.objects.filter(stuid=student_id)

    for x in queryset:
        item = {}
        activity = Activity.objects.get(id=x.activity_id)

        item['name'] = activity.name
        item['start_time'] = activity.start_time
        item['end_time'] = activity.end_time
        item['place'] = activity.place
        item['seat'] = x.seat
        item['valid'] = x.status
        item['unique_id'] = x.unique_id
        orders.append(item)

    return render_to_response('order_list.html', {
        'orders': orders,
        'stuid': student_id
    }, context_instance=RequestContext(request))


def print_ticket(request, unique_id):

    if not ('stuid' in request.session):
        return HttpResponseRedirect(s_reverse_order_index())

    try:
        ticket = Ticket.objects.get(unique_id=unique_id)
        activity = Activity.objects.get(id=ticket.activity_id)
        qr_addr = QRCODE_URL + "/fit/" + unique_id
    except ObjectDoesNotExist:
        raise Http404

    return render_to_response('print_ticket.html', {
        'qr_addr': qr_addr,
        'activity': activity,
        'stuid':ticket.stuid
    }, context_instance=RequestContext(request))


def adjust_menu_view(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())
    if not request.user.is_superuser:
        return HttpResponseRedirect(s_reverse_activity_list())
    activities = Activity.objects.filter(end_time__gt=datetime.now(), status=1)
    return render_to_response('adjust_menu.html', {
        'activities': activities,
    }, context_instance=RequestContext(request))


def custom_menu_get(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())
    if not request.user.is_superuser:
        return HttpResponseRedirect(s_reverse_activity_list())
    custom_buttons = get_custom_menu()
    current_menu = []
    for button in custom_buttons:
        sub_button = button.get('sub_button', [])
        if len(sub_button) > 0:
            temp_key = sub_button[0].get('key', '')
            if (not temp_key.startswith(WEIXIN_BOOK_HEADER + 'W')) and temp_key.startswith(WEIXIN_BOOK_HEADER):
                current_menu = sub_button
                break
    if auto_clear_old_menus(current_menu):
        modify_custom_menu(json.dumps(get_custom_menu_with_book_acts(current_menu), ensure_ascii=False).encode('utf8'))
    wrap_menu = []
    for menu in current_menu:
        wrap_menu += [{
            'name': menu['name'],
            'id': int(menu['key'].split('_')[-1]),
        }]
    return HttpResponse(json.dumps(wrap_menu), content_type='application/json')


def custom_menu_modify_post(request):
    if not request.user.is_authenticated():
        raise Http404
    if not request.user.is_superuser:
        raise Http404
    if not request.POST:
        raise Http404
    if not ('menus' in request.POST):
        raise Http404
    menus = json.loads(request.POST.get('menus', ''))
    sub_button = []
    for menu in menus:
        sub_button += [{
            'type': 'click',
            'name': menu['name'],
            'key': 'TSINGHUA_BOOK_' + str(menu['id']),
            'sub_button': [],
        }]
    return HttpResponse(
        modify_custom_menu(json.dumps(get_custom_menu_with_book_acts(sub_button), ensure_ascii=False).encode('utf8')),
        content_type='application/json')


def activity_export_stunum(request, act_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(s_reverse_admin_home())
    try:
        activity = Activity.objects.get(id=act_id)
    except ObjectDoesNotExist:
        raise Http404

    tickets = Ticket.objects.filter(activity=activity)
    wb = xlwt.Workbook()

    def write_row(ws, row, data):
        for index, cell in enumerate(data):
            ws.write(row, index, cell)

    ws = wb.add_sheet(activity.name)
    row = 1
    write_row(ws, 0, [u'学号', u'状态', u'座位'])
    status_map = [u'已取消', u'未入场', u'已入场']
    for ticket in tickets:
        write_row(ws, row, [ticket.stuid, status_map[ticket.status], ticket.seat])
        row += 1
    # 定义Content-Disposition，让浏览器能识别，弹出下载框
    file_name = 'activity' + act_id + '.xls'
    agent = request.META.get('HTTP_USER_AGENT')
    if agent and re.search('MSIE', agent):
        response = HttpResponse(content_type="application/vnd.ms-excel")  # 解决ie不能下载的问题
        response['Content-Disposition'] = 'attachment; filename=%s' % urlquote(file_name)  # 解决文件名乱码/不显示的问题
    else:
        response = HttpResponse(content_type="application/ms-excel")  # 解决ie不能下载的问题
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)  # 解决文件名乱码/不显示的问题
    # 保存
    wb.save(response)
    return response
