#-*- coding:utf-8 -*-

import datetime
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import random
import string
import time
import urllib
import urllib2

from queryhandler.settings import QRCODE_URL
from queryhandler.weixin_msg import get_msg_create_time
from urlhandler.models import User, Activity, Ticket, Bind, Seat
from userpage.safe_reverse import *
from weixinlib import http_get
from weixinlib.settings import WEIXIN_OAUTH2_URL
from weixinlib.weixin_urls import WEIXIN_URLS


def home(request):
    return render_to_response('mobile_base.html')


###################### ABANDON ######################
# Validate Format:
# METHOD 1: learn.tsinghua
# url: https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp
# form: { userid:2011013236, userpass:***, submit1: 登录 }
# success: check substring 'loginteacher_action.jsp'
# validate: userid is number
def validate_through_learn(user_id, user_pass):
    req_data = urllib.urlencode({'user_id': user_id, 'user_pass': user_pass, 'submit1': u'登录'.encode('gb2312')})
    request_url = 'https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp'
    req = urllib2.Request(url=request_url, data=req_data)
    res_data = urllib2.urlopen(req)
    try:
        res = res_data.read()
    except:
        return 'Error'
    if 'loginteacher_action.jsp' in res:
        return 'Accepted'
    else:
        return 'Rejected'


# METHOD 2 is not valid, because student.tsinghua has not linked to Internet
# METHOD 2: student.tsinghua
# url: http://student.tsinghua.edu.cn/checkUser.do?redirectURL=%2Fqingxiaotuan.do
# form: { username:2011013236, password:encryptedString(***) }
# success: response response is null / check response status code == 302
# validate: username is number
def validate_through_student(userid, userpass):
    return 'Error'


def validate_post_auth(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'username' in request.POST) or (not 'password' in request.POST):
        raise Http404
    openid = request.POST['openid']
    userid = request.POST['username']
    if not userid.isdigit():
        raise Http404
    secret = request.POST['password']
    validate_result = validate_through_auth(secret)
    if validate_result['result'] == 'Accepted':
        try:
            User.objects.filter(stu_id=userid).update(status=0)
            User.objects.filter(weixin_id=openid).update(status=0)
        except:
            return HttpResponse('Error')
        try:
            current_user = User.objects.get(stu_id=userid)
            current_user.weixin_id = openid
            current_user.status = 1
            current_user.stu_name = validate_result['name']
            current_user.stu_type = validate_result['type']
            try:
                current_user.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                new_user = User.objects.create(
                    weixin_id=openid,
                    stu_id=userid,
                    stu_name=validate_result['name'],
                    stu_type=validate_result['type'],
                    status=1)
                new_user.save()
            except:
                return HttpResponse('Error')
    return HttpResponse(validate_result['result'])


def validate_post(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'username' in request.POST) or (not 'password' in request.POST):
        raise Http404
    user_id = request.POST['username']
    if not user_id.isdigit():
        raise Http404
    user_pass = request.POST['password'].encode('gb2312')
    validate_result = validate_through_learn(user_id, user_pass)
    if validate_result == 'Accepted':
        openid = request.POST['openid']
        try:
            User.objects.filter(stu_id=user_id).update(status=0)
            User.objects.filter(weixin_id=openid).update(status=0)
        except:
            return HttpResponse('Error')
        try:
            current_user = User.objects.get(stu_id=user_id)
            current_user.weixin_id = openid
            current_user.status = 1
            try:
                current_user.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                new_user = User.objects.create(weixin_id=openid, stu_id=user_id, status=1)
                new_user.save()
            except:
                return HttpResponse('Error')
    return HttpResponse(validate_result)
###################### ABANDON ######################


def validate_view(request, openid):
    if User.objects.filter(weixin_id=openid, status=1).exists():
        is_validated = 1
    else:
        is_validated = 0
    student_id = ''
    if request.GET:
        student_id = request.GET.get('student_id', '')
    return render_to_response('tt_validation.html', {
        'openid': openid,
        'student_id': student_id,
        'isValidated': is_validated,
        'now': datetime.datetime.now() + datetime.timedelta(seconds=-5),
    }, context_instance=RequestContext(request))


def validate_get_time_auth(request):
    request_url = "http://auth.igeek.asia/v1/time"
    req = urllib2.Request(url=request_url)
    res_data = urllib2.urlopen(req)
    try:
        res = res_data.read()
    except:
        return 'Error'
    return HttpResponse(res)


def validate_through_auth(secret):
    req_data = urllib.urlencode({'secret': secret})
    request_url = 'http://auth.igeek.asia/v1'
    req = urllib2.Request(url=request_url, data=req_data)
    res_data = urllib2.urlopen(req)
    try:
        res = res_data.read()
        res_dict = json.loads(res)
    except:
        return {
            'result': 'Error'
        }
    if res_dict['code'] == 0:
        return {
            'result': 'Accepted',
            'name': res_dict['data']['name'],
            'type': res_dict['data']['usertype']
        }
    else:
        return {
            'result': 'Rejected'
        }


def uc_validate_post_auth(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'username' in request.POST) or (not 'password' in request.POST):
        raise Http404
    openid = request.POST['openid']
    user_id = request.POST['username']
    if not user_id.isdigit():
        raise Http404
    secret = request.POST['password']
    validate_result = validate_through_auth(secret)
    if validate_result['result'] == 'Accepted':
        if not validate_result['type']:
            validate_result['type'] = "教师"
        try:
            User.objects.filter(stu_id=user_id).update(status=0)
            User.objects.filter(weixin_id=openid).update(status=0)
        except:
            return HttpResponse('Error')
        try:
            current_user = User.objects.get(stu_id=user_id)
            current_user.weixin_id = openid
            current_user.status = 1
            current_user.stu_name = validate_result['name']
            current_user.stu_type = validate_result['type']
            current_user.bind_count = 0
            try:
                current_user.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                new_user = User.objects.create(
                    weixin_id=openid,
                    stu_id=user_id,
                    stu_name=validate_result['name'],
                    stu_type=validate_result['type'],
                    status=1)
                new_user.save()
            except:
                return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_account(openid))
    return HttpResponse(validate_result['result'])


###################### Activity Detail ######################

def details_view(request, activityid):
    activity = Activity.objects.filter(id=activityid)
    if not activity.exists():
        raise Http404    #current activity is invalid
    act_name = activity[0].name
    act_key = activity[0].key
    act_place = activity[0].place
    act_book_start = activity[0].book_start
    act_book_end = activity[0].book_end
    act_begin_time = activity[0].start_time
    act_end_time = activity[0].end_time
    act_total_tickets = activity[0].total_tickets
    act_text = activity[0].description
    act_ticket_remain = activity[0].remain_tickets
    act_abstract = act_text
    MAX_LEN = 256
    act_text_status = 0
    if len(act_text) > MAX_LEN:
        act_text_status = 1
        act_abstract = act_text[0:MAX_LEN]+u'...'
    act_photo = activity[0].pic_url
    cur_time = timezone.now()  # use the setting UTC
    act_seconds = 0
    if act_book_start <= cur_time <= act_book_end:
        act_delta = act_book_end - cur_time
        act_seconds = act_delta.total_seconds()
        act_status = 0  # during book time
    elif cur_time < act_book_start:
        act_delta = act_book_start - cur_time
        act_seconds = act_delta.total_seconds()
        act_status = 1  # before book time
    else:
        act_status = 2  # after book time
    variables = RequestContext(request, {'act_name': act_name, ' act_text': act_text, 'act_photo': act_photo,
                                         'act_book_start': act_book_start, 'act_book_end': act_book_end,
                                         'act_begin_time': act_begin_time, 'act_end_time': act_end_time,
                                         'act_totaltickets': act_total_tickets, 'act_key': act_key,
                                         'act_place': act_place, 'act_status': act_status, 'act_seconds': act_seconds,
                                         'cur_time': cur_time, 'act_abstract': act_abstract,
                                         'act_text_status': act_text_status, 'act_ticket_remain': act_ticket_remain})
    return render_to_response('activitydetails.html', variables)


def ticket_view(request, uid):
    ticket = Ticket.objects.filter(unique_id=uid)
    if not ticket.exists():
        information = "票已过期"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {
            'information': information,
            'href': href
        }) #current activity is invalid
    activity = Activity.objects.filter(id=ticket[0].activity_id)
    act_id = activity[0].id
    act_name = activity[0].name
    act_key = activity[0].key
    act_begin_time = activity[0].start_time
    act_end_time = activity[0].end_time
    act_place = activity[0].place
    ticket_status = ticket[0].status
    now = datetime.datetime.now()
    if act_end_time < now:#表示活动已经结束
        ticket_status = 3
    ticket_seat = ticket[0].seat
    if activity[0].seat_status == 1:
        ticket_url = s_reverse_ticket_select_zongti(uid)
    else:
        ticket_url = s_reverse_ticket_selection(uid)
    act_photo = QRCODE_URL + "/fit/" + uid
    href = WEIXIN_OAUTH2_URL
    variables = RequestContext(request, {
        'act_id': act_id,
        'act_name': act_name,
        'act_place': act_place,
        'act_begin_time': act_begin_time,
        'act_end_time': act_end_time,
        'act_photo': act_photo,
        'ticket_status': ticket_status,
        'ticket_seat': ticket_seat,
        'act_key': act_key,
        'ticket_url': ticket_url,
        'href': href
    })
    return render_to_response('activityticket.html', variables)


def help_view(request):
    variables = RequestContext(request, {'name': u'“紫荆之声”'})
    return render_to_response('help.html', variables)


def activity_menu_view(request, act_id):
    activity = Activity.objects.get(id=act_id)
    return render_to_response('activitymenu.html', {'activity': activity})


def helpact_view(request):
    variables = RequestContext(request, {})
    return render_to_response('help_activity.html', variables)


def helpclub_view(request):
    variables = RequestContext(request, {})
    return render_to_response('help_club.html', variables)


def helplecture_view(request):
    variables = RequestContext(request, {})
    return render_to_response('help_lecture.html', variables)


def uc_center(request):
    code = request.GET.get('code')
    url = WEIXIN_URLS['get_openid'](code)
    res = http_get(url)
    r_json = json.loads(res)
    openid = r_json['openid']
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        return redirect(s_reverse_uc_ticket(openid))
    else:
        return redirect(s_reverse_uc_account(openid))


def uc_account(request, openid):
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        if request.method == 'POST':
            try:
                binds1 = Bind.objects.filter(active_stu_id=user[0].stu_id)
                for bind in binds1:
                    user.update(bind_count=F('bind_count')-1)
                    User.objects.filter(stu_id=bind.passive_stu_id, status=1).update(bind_count=F('bind_count')-1)
                binds1.delete()
                binds2 = Bind.objects.filter(passive_stu_id=user[0].stu_id)
                for bind in binds2:
                    user.update(bind_count=F('bind_count')-1)
                    User.objects.filter(stu_id=bind.active_stu_id, status=1).update(bind_count=F('bind_count')-1)
                binds2.delete()
                user.update(status=0)
            except:
                return HttpResponse('logout error')
            return render_to_response('usercenter_account_login.html', {'weixin_id': openid}, context_instance=RequestContext(request))
        else:
            return render_to_response('usercenter_account.html', {
                'weixin_id': openid,
                'student_id': user[0].stu_id,
                'student_name': user[0].stu_name,
                'student_type': user[0].stu_type
            }, context_instance=RequestContext(request))
    else:
        return render_to_response('usercenter_account_login.html', {'weixin_id': openid}, context_instance=RequestContext(request))


@csrf_exempt
def uc_ticket(request, openid):
    if request.method == 'POST':
        if request.POST.get('ticket_uid', ''):
            ticket_uid = request.POST['ticket_uid']
            ticket_url = s_reverse_ticket_detail(ticket_uid)
            seat_url = s_reverse_ticket_selection(ticket_uid)
            rtn_json = {'ticketURL': ticket_url, 'seatURL': seat_url}
            return HttpResponse(json.dumps(rtn_json), content_type='application/json')
    if request.is_ajax():
        try:
            if not request.POST.get('ticket_id', ''):
                return HttpResponse('logout error')
            else:
                ticket_id = request.POST['ticket_id']
                tickets = Ticket.objects.filter(unique_id=ticket_id)
                if not tickets.exists():
                    return HttpResponse('logout error')
                else:
                    ticket = tickets[0]
                    ticket.status = 0
                    ticket.save()
                    seat = ticket.seat.split('-')
                    activity = ticket.activity
                    if len(seat) > 1:
                        row = int(seat[0]) - 1
                        column = int(seat[1]) - 1
                        seat_table = json.loads(activity.seat_table)
                        seat_table[row][column] = 1
                        Activity.objects.filter(id=activity.id).update(seat_table=json.dumps(seat_table))
                    Activity.objects.filter(id=activity.id).update(remain_tickets=F('remain_tickets')+1)
                return HttpResponse('logout error')
        except:
            return HttpResponse('logout error')
    tickets = []
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        is_validated = 1
        tickets = Ticket.objects.filter(stu_id=user[0].stu_id, status=1)
    else:
        is_validated = 0
    return render_to_response('usercenter_ticket.html', {'tickets': tickets,
                                                         'isValidated': is_validated, 'weixin_id': openid})


def encode_token(openid):
    user = User.objects.filter(weixin_id=openid, status=1)
    timestamp = int(time.time()) / 100
    token = int(user[0].stu_id) ^ timestamp
    return token


def decode_token(token):
    if not token.isdigit():
        return '-1'
    timestamp = int(time.time()) / 100
    stu_id = str(int(token) ^ timestamp)
    return stu_id


def uc_2ticket_bind(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'activity_name' in request.POST) or (not 'token' in request.POST):
        raise Http404
    openid = request.POST['openid']
    user = User.objects.filter(weixin_id=openid, status=1)
    if not user:
        raise Http404
    active_stu_id = user[0].stu_id
    activity = Activity.objects.filter(name=request.POST['activity_name'], status=1)
    if not activity:
        raise Http404
    passive_stu_id = decode_token(request.POST['token'])
    if active_stu_id == passive_stu_id:
        return HttpResponse('SameStudentID')
    if not User.objects.filter(stu_id=passive_stu_id, status=1).exists():
        return HttpResponse('TokenError')
    if Ticket.objects.filter(stu_id=passive_stu_id, activity=activity[0], status=1).exists():
        return HttpResponse('HaveTicket')
    if Bind.objects.filter(activity=activity[0], active_stu_id=passive_stu_id) or \
            Bind.objects.filter(activity=activity[0], passive_stu_id=passive_stu_id):
        return HttpResponse('AlreadyBinded')
    else:
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        while Bind.objects.filter(unique_id=random_string).exists():
            random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        try:
            newbind = Bind.objects.create(activity=activity[0], active_stu_id=active_stu_id, passive_stu_id=passive_stu_id, unique_id=random_string)
            newbind.save()
            User.objects.filter(stu_id=active_stu_id, status=1).update(bind_count=F('bind_count')+1)
            User.objects.filter(stu_id=passive_stu_id, status=1).update(bind_count=F('bind_count')+1)
        except:
            return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_2ticket(openid))


@csrf_exempt
def uc_2ticket(request, openid):
    if request.is_ajax():
        try:
            bind = Bind.objects.filter(unique_id=request.POST['unique_id'])
            User.objects.filter(stu_id=bind[0].active_stu_id, status=1).update(bind_count=F('bind_count')-1)
            User.objects.filter(stu_id=bind[0].passive_stu_id, status=1).update(bind_count=F('bind_count')-1)
            bind.delete()
            return HttpResponse('Success')
        except:
            return HttpResponse('Error')
    else:
        user = User.objects.filter(weixin_id=openid, status=1)
        if user:
            is_validated = 1
            binds = Bind.objects.filter(Q(active_stu_id=user[0].stu_id) | Q(passive_stu_id=user[0].stu_id))
            tickets = Ticket.objects.filter(stu_id=user[0].stu_id, status=1)
            now = datetime.datetime.now()
            aty_can_bind = Activity.objects.filter(status=1, end_time__gt=now, book_start__lt=now)
            return render_to_response('usercenter_2ticket.html', {
                'isValidated': is_validated,
                'weixin_id': openid,
                'stu_id': user[0].stu_id,
                'aty_canBind': aty_can_bind,
                'binds': binds,
                'tickets': tickets
            }, context_instance=RequestContext(request))
        else:
            is_validated = 0
            return render_to_response('usercenter_2ticket.html', {
                'isValidated': is_validated,
                'weixin_id': openid
            }, context_instance=RequestContext(request))


@csrf_exempt
def uc_token(request, openid):
    if request.is_ajax():
        token = encode_token(request.POST.get('openid', ''))
        rtn_json = {'token': token}
        return HttpResponse(json.dumps(rtn_json), content_type='application/json')
    else:
        if User.objects.filter(weixin_id=openid, status=1).exists():
            is_validated = 1
        else:
            is_validated = 0
        return render_to_response('usercenter_token.html', {'isValidated': is_validated, 'weixin_id': openid})


@csrf_exempt
def views_seats(request, uid):
    if not request.POST:
        rtn_json = {}
        ticket = Ticket.objects.filter(unique_id=uid, status=1)
        if not ticket.exists():
            seats_list = []
        else:
            seats_list = json.loads(ticket[0].activity.seat_table)
        ticket_id = uid
        act_title = ticket[0].activity.name
        act_place = ticket[0].activity.place
        act_time = ticket[0].activity.start_time
        ticket_type = ticket[0].partner_id
        return render_to_response('seats.html', locals())
    else:
        rtn_json = {}
        ticket_id = request.POST.get('ticketID', '')
        post_select = request.POST.get('postSelect', '')

        try:
            ticket = Ticket.objects.get(unique_id=ticket_id, status=1)
        except:
            rtn_json['msg'] = 'invalidTicket'
            return HttpResponse(json.dumps(rtn_json), content_type='application/json')

        seats = post_select.split(',')
        seat = seats[0]
        row = int(seat.split("-")[0]) - 1
        column = int(seat.split("-")[1]) - 1

        if len(seats) > 1:
            other_seat = seats[1]
            other_row = int(other_seat.split("-")[0]) - 1
            other_column = int(other_seat.split("-")[1]) - 1
            other_stu_id = ticket.partner_id

        activity_name = ticket.activity.name

        with transaction.atomic():
            if len(seats) > 1:
                activity = Activity.objects.select_for_update().filter(name=activity_name)
                seats_table = json.loads(activity[0].seat_table)
                ticket = Ticket.objects.select_for_update().filter(status=1, seat=seat)
                other_ticket = Ticket.objects.filter(status=1, seat=other_seat)
                if ticket.exists() or other_ticket.exists():
                    rtn_json['seat'] = seats_table
                    rtn_json['msg'] = 'invalidSeat'
                    return HttpResponse(json.dumps(rtn_json), content_type='application/json')
                else:
                    seats_table[row][column] = 2
                    seats_table[other_row][other_column] = 2
                    seats_list = json.dumps(seats_table)
                    activity = Activity.objects.filter(name=activity_name)
                    Ticket.objects.filter(unique_id=ticket_id).update(seat=seat)
                    Ticket.objects.filter(stu_id=other_stu_id, activity=activity[0]).update(seat=other_seat)
                    activity.update(seat_table=seats_list)
                    rtn_json['seat'] = seats_table
                    rtn_json['msg'] = 'success'
                    rtn_json['next_url'] = s_reverse_ticket_detail(uid)
                    return HttpResponse(json.dumps(rtn_json), content_type='application/json')
            else:
                activity = Activity.objects.select_for_update().filter(name=activity_name)
                seats_table = json.loads(activity[0].seat_table)
                ticket = Ticket.objects.select_for_update().filter(status=1, seat=seat)
                if ticket.exists():
                    rtn_json['seat'] = seats_table
                    rtn_json['msg'] = 'invalidSeat'
                    return HttpResponse(json.dumps(rtn_json), content_type='application/json')
                else:
                    seats_table[row][column] = 2
                    seats_list = json.dumps(seats_table)
                    Ticket.objects.filter(unique_id=ticket_id).update(seat=seat)
                    Activity.objects.filter(name=activity_name).update(seat_table=seats_list)
                    rtn_json['seat'] = seats_table
                    rtn_json['msg'] = 'success'
                    rtn_json['next_url'] = s_reverse_ticket_detail(uid)
                    return HttpResponse(json.dumps(rtn_json), content_type='application/json')


def views_seats_zongti(request, uid):
    ticket = Ticket.objects.filter(unique_id=uid, status=1)
    if not ticket.exists():
        information = "该票无效"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {'information': information, 'href': href})
    else:
        ticket_id = str(uid)
        book_time = "this is time"
        ticket_type = ticket[0].partner_id
        ticket_left = get_seat_left(uid)
        return render_to_response('seats_zongti.html', locals())


@csrf_exempt
def select_seats_zongti_post(request):
    if not request.POST:
        information = "出了点莫名其妙的错误"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {'information': information, 'href': href})
    post = request.POST
    return_json = dict()
    try:
        section = post['section']
        ticket = Ticket.objects.get(unique_id=post['ticket_id'])
        ticket_left = Seat.objects.filter(seat_section=post['section'], is_selected=0, activity=ticket.activity)
        if (not ticket_left.exists() and ticket.partner_id == 's') or (ticket.partner_id != "s" and len(ticket_left) < 2):
            return_json['msg'] = 'NoSeat'
            return_json['seat_left'] = json.dumps(get_seat_left(post['ticket_id']))
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        seat = section_select(post)
        if seat == None:
            print "error"
            return_json['msg'] = 'error'
        else:
            print "success"
            return_json['msg'] = 'success'
            return_json['next_url'] = s_reverse_ticket_detail(post['ticket_id'])
        return HttpResponse(json.dumps(return_json), content_type='application/json')
    except Exception as e:
        information = "出了点莫名其妙的错误"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {'information': information, 'href': href})


def get_seat_left(uid):
    try:
        ticket = Ticket.objects.get(unique_id=uid)
    except Exception as e:
        return None
    ticket_left = dict()
    seats_in_section_a = Seat.objects.filter(seat_section='A', is_selected=0, activity=ticket.activity)
    ticket_left['A'] = len(seats_in_section_a)
    seats_in_section_b = Seat.objects.filter(seat_section='B', is_selected=0, activity=ticket.activity)
    ticket_left['B'] = len(seats_in_section_b)
    seats_in_section_c = Seat.objects.filter(seat_section='C', is_selected=0, activity=ticket.activity)
    ticket_left['C'] = len(seats_in_section_c)
    seats_in_section_d = Seat.objects.filter(seat_section='D', is_selected=0, activity=ticket.activity)
    ticket_left['D'] = len(seats_in_section_d)
    seats_in_section_e = Seat.objects.filter(seat_section='E', is_selected=0, activity=ticket.activity)
    ticket_left['E'] = len(seats_in_section_e)
    return ticket_left


def section_select(post):
    with transaction.atomic():
        try:
            ticket = Ticket.objects.get(unique_id=post['ticket_id'])
        except Exception as e:
            return None
        seats = Seat.objects.select_for_update().filter(seat_section=post['section'], is_selected=0, activity=ticket.activity)
        if not seats.exists():
            return None
        if ticket.partner_id != "s":
            if len(seats) < 2:
                return None
            try:
                partner_ticket = Ticket.objects.get(stu_id=ticket.partner_id, activity=ticket.activity)
            except Exception as e:
                return None
        seat = seats[0]
        ticket.seat = post['section']
        ticket.save()
        seat.is_selected = 1
        seat.save()
        if ticket.partner_id != "s":
            partner_ticket.seat = post['section']
            partner_ticket.save()
            partner_seat = seats[1]
            partner_seat.is_selected = 1
            partner_seat.save()
        return seat


def select_xinqing_post(request):
    if not request.POST:
        information = "出了点莫名其妙的错误"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {'information': information, 'href': href})
    post = request.POST
    return_json = dict()
    #seat info format: "section1-row1-column1,[section2-row2-column2,]"
    try:
        seats_selected = post['seat'].split(',')
        ticket = Ticket.objects.get(unique_id=post['ticket_id'])
        activity = ticket.activity
        now = datetime.datetime.now()
        if activity.start_time < now or activity.status != 1:
            return_json['msg'] = 'WrongActivity'
            return_json['seat_left'] = json.dumps(get_valid_seat(post['ticket_id']))
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        seat = seats_select(seats_selected, ticket, activity)
        if seat == None:
            print "error"
            return_json['msg'] = 'error'
        else:
            print "success"
            return_json['msg'] = 'success'
            return_json['next_url'] = s_reverse_ticket_detail(post['ticket_id'])
        return HttpResponse(json.dumps(return_json), content_type='application/json')
    except Exception:
        information = "出了点莫名其妙的错误"
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {'information': information, 'href': href})


def get_valid_seat(uid):
    valid_seat_list = []
    try:
        ticket = Ticket.objects.get(unique_id=uid)
    except Exception:
        return valid_seat_list
    seats = Seat.objects.get(activity=ticket.activity)
    for seat in seats:
        seat_info = seat.seat_section + '-' + seat.position_row + "-" + seat.position_column
        valid_seat_list.append(seat_info)
    return valid_seat_list


def seats_select(seats_selected, ticket, activity):
    with transaction.atomic():
        seat_1 = seats_selected[0].split('-')
        section_1 = seat_1[0]
        row_1 = seat_1[1]
        column_1 = seat_1[2]
        seat_1_db = Seat.objects.select_for_update().filter(position_row=row_1,
                                                            position_column=column_1,
                                                            seat_section=section_1,
                                                            is_selected=0,
                                                            activity=activity)
        if not seat_1_db.exists():
            return None
        if len(seats_selected) > 2:
            try:
                partner_ticket = Ticket.objects.get(stu_id=ticket.partner_id,
                                                    activity=ticket.activity)
            except Exception:
                return None
            seat_2 = seats_selected[2].split('-')
            section_2 = seat_2[0]
            row_2 = seat_2[1]
            column_2 = seat_2[2]
            seat_2_db = Seat.objects.filter(position_row=row_2,
                                            position_column=column_2,
                                            seat_section=section_2,
                                            is_selected=0,
                                            activity=activity)
            return_json = {}
            if not seat_2_db.exists():
                return_json['msg'] = 'NoSeat'
                return_json['seat_left'] = json.dumps(get_valid_seat(ticket.unique_id))
                return None
            seat = seat_2_db[0]
            seat.save()
            partner_ticket.seat = seat_2
            partner_ticket.save()
        seat = seat_1_db[0]
        seat.is_selected = 1
        seat.save()
        ticket.seat = seat_1
        ticket.save()
        return seat
