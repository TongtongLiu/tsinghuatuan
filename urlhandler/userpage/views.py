#-*- coding:utf-8 -*-
from django.db.models import Q

from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from urlhandler.models import User, Activity, Ticket, Bind
from django.views.decorators.csrf import csrf_exempt
from urlhandler.settings import STATIC_URL
import urllib, urllib2
import datetime, time
import json
from django.db import transaction
from django.utils import timezone
from weixinlib.weixin_urls import WEIXIN_URLS
from weixinlib import http_get
from django.shortcuts import redirect
from userpage.safe_reverse import *
import string
import random

def home(request):
    return render_to_response('mobile_base.html')


###################### Validate ######################
# request.GET['openid'] must be provided.
def validate_view(request, openid):
    if User.objects.filter(weixin_id=openid, status=1).exists():
        isValidated = 1
    else:
        isValidated = 0
    studentid = ''
    if request.GET:
        studentid = request.GET.get('studentid', '')
    return render_to_response('tt_validation.html', {
        'openid': openid,
        'studentid': studentid,
        'isValidated': isValidated,
        'now': datetime.datetime.now() + datetime.timedelta(seconds=-5),
    }, context_instance=RequestContext(request))


# Validate Format:
# METHOD 1: learn.tsinghua
# url: https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp
# form: { userid:2011013236, userpass:***, submit1: 登录 }
# success: check substring 'loginteacher_action.jsp'
# validate: userid is number
def validate_through_learn(userid, userpass):
    req_data = urllib.urlencode({'userid': userid, 'userpass': userpass, 'submit1': u'登录'.encode('gb2312')})
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
        res_dict = eval(res)
    except:
        return {
            'result': 'Error'
        }
    if res_dict['code'] == 0:
        print
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
            currentUser = User.objects.get(stu_id=userid)
            currentUser.weixin_id = openid
            currentUser.status = 1
            currentUser.stu_name = validate_result['name']
            currentUser.stu_type = validate_result['type']
            currentUser.bind_count = 0
            try:
                currentUser.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                newuser = User.objects.create(weixin_id=openid, stu_id=userid, stu_name=validate_result['name'], stu_type=validate_result['type'], status=1)
                newuser.save()
            except:
                return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_account(openid))
    return HttpResponse(validate_result['result'])


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
            currentUser = User.objects.get(stu_id=userid)
            currentUser.weixin_id = openid
            currentUser.status = 1
            currentUser.stu_name = validate_result['name']
            currentUser.stu_type = validate_result['type']
            try:
                currentUser.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                newuser = User.objects.create(weixin_id=openid, stu_id=userid, stu_name=validate_result['name'], stu_type=validate_result['type'], status=1)
                newuser.save()
            except:
                return HttpResponse('Error')
    return HttpResponse(validate_result['result'])


def validate_post(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'username' in request.POST) or (not 'password' in request.POST):
        raise Http404
    userid = request.POST['username']
    if not userid.isdigit():
        raise Http404
    userpass = request.POST['password'].encode('gb2312')
    validate_result = validate_through_learn(userid, userpass)
    if validate_result == 'Accepted':
        openid = request.POST['openid']
        try:
            User.objects.filter(stu_id=userid).update(status=0)
            User.objects.filter(weixin_id=openid).update(status=0)
        except:
            return HttpResponse('Error')
        try:
            currentUser = User.objects.get(stu_id=userid)
            currentUser.weixin_id = openid
            currentUser.status = 1
            try:
                currentUser.save()
            except:
                return HttpResponse('Error')
        except:
            try:
                newuser = User.objects.create(weixin_id=openid, stu_id=userid, status=1)
                newuser.save()
            except:
                return HttpResponse('Error')
    return HttpResponse(validate_result)


###################### Activity Detail ######################

def details_view(request, activityid):
    activity = Activity.objects.filter(id=activityid)
    if not activity.exists():
        raise Http404  #current activity is invalid
    act_name = activity[0].name
    act_key = activity[0].key
    act_place = activity[0].place
    act_bookstart = activity[0].book_start
    act_bookend = activity[0].book_end
    act_begintime = activity[0].start_time
    act_endtime = activity[0].end_time
    act_totaltickets = activity[0].total_tickets
    act_text = activity[0].description
    act_ticket_remian = activity[0].remain_tickets
    act_abstract = act_text
    MAX_LEN = 256
    act_text_status = 0
    if len(act_text) > MAX_LEN:
        act_text_status = 1
        act_abstract = act_text[0:MAX_LEN]+u'...'
    act_photo = activity[0].pic_url
    cur_time = timezone.now() # use the setting UTC
    act_seconds = 0
    if act_bookstart <= cur_time <= act_bookend:
        act_delta = act_bookend - cur_time
        act_seconds = act_delta.total_seconds()
        act_status = 0 # during book time
    elif cur_time < act_bookstart:
        act_delta = act_bookstart - cur_time
        act_seconds = act_delta.total_seconds()
        act_status = 1 # before book time
    else:
        act_status = 2 # after book time
    variables=RequestContext(request,{'act_name':act_name,'act_text':act_text, 'act_photo':act_photo,
                                      'act_bookstart':act_bookstart,'act_bookend':act_bookend,'act_begintime':act_begintime,
                                      'act_endtime':act_endtime,'act_totaltickets':act_totaltickets,'act_key':act_key,
                                      'act_place':act_place, 'act_status':act_status, 'act_seconds':act_seconds,'cur_time':cur_time,
                                      'act_abstract':act_abstract, 'act_text_status':act_text_status,'act_ticket_remian':act_ticket_remian})
    return render_to_response('activitydetails.html', variables)


def ticket_view(request, uid):
    ticket = Ticket.objects.filter(unique_id=uid)
    if not ticket.exists():
        raise Http404  #current activity is invalid
    activity = Activity.objects.filter(id=ticket[0].activity_id)
    act_id = activity[0].id
    act_name = activity[0].name
    act_key = activity[0].key
    act_begintime = activity[0].start_time
    act_endtime = activity[0].end_time
    act_place = activity[0].place
    ticket_status = ticket[0].status
    now = datetime.datetime.now()
    if act_endtime < now:#表示活动已经结束
        ticket_status = 3
    ticket_seat = ticket[0].seat
    if ticket_seat == '':
        ticket_url = s_reverse_ticket_selection(uid)
    else:
        ticket_url = ''
    act_photo = "http://qr.ssast.org/fit/"+uid
    variables=RequestContext(request,{'act_id':act_id, 'act_name':act_name,'act_place':act_place, 'act_begintime':act_begintime,
                                      'act_endtime':act_endtime,'act_photo':act_photo, 'ticket_status':ticket_status,
                                      'ticket_seat':ticket_seat,
                                      'act_key':act_key,
                                      'ticket_url':ticket_url})
    return render_to_response('activityticket.html', variables)

def help_view(request):
    variables=RequestContext(request,{'name':u'“紫荆之声”'})
    return render_to_response('help.html', variables)


def activity_menu_view(request, actid):
    activity = Activity.objects.get(id=actid)
    return render_to_response('activitymenu.html', {'activity': activity})

def helpact_view(request):
    variables=RequestContext(request,{})
    return render_to_response('help_activity.html', variables)

def helpclub_view(request):
    variables=RequestContext(request,{})
    return render_to_response('help_club.html', variables)

def helplecture_view(request):
    variables=RequestContext(request,{})
    return render_to_response('help_lecture.html', variables)

def uc_center(request):
    code = request.GET.get('code')
    url = WEIXIN_URLS['get_openid'](code)
    res = http_get(url)
    rjson = json.loads(res)
    openid = rjson['openid']
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        return redirect(s_reverse_uc_ticket(openid))
    else:
        return redirect(s_reverse_uc_account(openid))

@csrf_exempt
def uc_ticket(request, openid):
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
                Ticket.objects.filter(unique_id=ticket_id).delete()
                return HttpResponse('logout error')
        except:
            return HttpResponse('logout error')
    tickets = []
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        isValidated = 1
        tickets = Ticket.objects.filter(stu_id=user[0].stu_id, status=1)
    else:
        isValidated = 0
    return render_to_response('usercenter_ticket.html', {'tickets':tickets,
                                                         'isValidated':isValidated, 'weixin_id':openid})


def uc_account(request, openid):
    user = User.objects.filter(weixin_id=openid, status=1)
    if user:
        if request.method == 'POST':
            try:
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


def encode_token(openid):
    user = User.objects.filter(weixin_id=openid, status=1)
    timestamp = int(time.time()) / 100
    token = int(user[0].stu_id) ^ timestamp
    return token


def decode_token(token):
    timestamp = int(time.time()) / 100
    stu_id = int(token) ^ timestamp
    return stu_id


def uc_2ticket_bind(request):
    if (not request.POST) or (not 'openid' in request.POST) or \
            (not 'activity' in request.POST) or (not 'token' in request.POST):
        raise Http404
    openid = request.POST['openid']
    user = User.objects.filter(weixin_id=openid)
    if not user:
        raise Http404
    active_stu_id = user[0].stu_id
    activity = Activity.objects.filter(name=request.POST['activity_name'])
    if not activity:
        raise Http404
    passive_stu_id = decode_token(request.POST['token'])
    if not User.objects.filter(stu_id=passive_stu_id):
        raise HttpResponse('TokenError')
    if Bind.objects.filter(activity=activity, active_stu_id=passive_stu_id) or Bind.objects.filter(activity=activity, passive_stu_id=passive_stu_id):
        return HttpResponse('AlreadyBinded')
    else:
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        while Bind.objects.filter(unique_id=random_string).exists():
            random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
            print random_string
        try:
            newbind = Bind.objects.create(activity=activity, activie_stu_id=active_stu_id, passive_stu_id=passive_stu_id, unique_id=random_string)
            newbind.save()
            User.objects.filter(stu_id=active_stu_id).update(bind_count=F('bind_count')+1)
            User.objects.filter(stu_id=passive_stu_id).update(bind_count=F('bind_count')+1)
        except:
            return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_2ticket(openid))

@csrf_exempt
def uc_2ticket(request, openid):
    if request.is_ajax():
        try:
            if not request.POST.get('unique_id', ''):
                return HttpResponse('logout error')
            else:
                unique_id = request.POST['unique_id']
                bind = Bind.objects.filter(unique_id=unique_id)
                User.objects.filter(stu_id=bind[0].active_stu_id).update(bind_count=F('bind_count')-1)
                User.objects.filter(stu_id=bind[0].passive_stu_id).update(bind_count=F('bind_count')-1)
                bind.delete()
                return HttpResponse('logout error')
        except:
            return HttpResponse('logout error')
    else:
        user = User.objects.filter(weixin_id=openid, status=1)
        if user:
            isValidated = 1
            binds = Bind.objects.filter(Q(active_stu_id=user[0].stu_id) | Q(passive_stu_id=user[0].stu_id))
            aty_canBind = Activity.objects.filter(status=1)
            return render_to_response('usercenter_2ticket.html', {
                'isValidated': isValidated,
                'weixin_id': openid,
                'stu_id': user[0].stu_id,
                'aty_canBind': aty_canBind,
                'binds': binds
            }, context_instance=RequestContext(request))
        else:
            isValidated = 0
            return render_to_response('usercenter_2ticket.html', {
                'isValidated': isValidated,
                'weixin_id': openid
            }, context_instance=RequestContext(request))

@csrf_exempt
def uc_token(request, openid):
    if request.method == 'POST':
        token = encode_token(request.POST.get('openid', ''))
        rtnJSON = {'token': token}
        return HttpResponse(json.dumps(rtnJSON), content_type='application/json')
    else:
        if User.objects.filter(weixin_id=openid, status=1).exists():
            isValidated = 1
        else:
            isValidated = 0
        return render_to_response('usercenter_token.html',{'isValidated':isValidated, 'weixin_id':openid})

@csrf_exempt
def views_seats(request, uid):
    if not request.POST:
        rtnJSON = {}
        ticket = Ticket.objects.filter(unique_id=uid, status=1)
        if not ticket.exists():
            seats_list = []
        else:
            seats_list = json.loads(ticket[0].activity.seat_table)
        ticketID = uid
        title = ticket[0].activity.name
        time = ticket[0].activity.start_time
        ticket_type = ticket[0].partner_id
        return render_to_response('seats.html', locals())
    else:
        rtnJSON = {}
        ticketID = request.POST.get('ticketID', '')
        postSelect = request.POST.get('postSelect', '')

        try:
            ticket = Ticket.objects.get(unique_id=ticketID, status=1)
        except:
            rtnJSON['msg'] = 'invalidTicket'
            return HttpResponse(json.dumps(rtnJSON), content_type='application/json')

        seats = postSelect.split(',')
        seat = seats[0]
        row = int(seat.split("-")[0]) - 1
        column = int(seat.split("-")[1]) - 1
       
        if len(seats) > 1:
            other_seat = seats[1]
            other_row = int(other_seat.split("-")[0]) - 1
            other_column = int(other_seat.split("-")[1]) - 1
            other_stu_id = ticket.partner_id

        activityName = ticket.activity.name
        
        with transaction.atomic():
            if len(seats) > 1:
                activity = Activity.objects.select_for_update().filter(name = activityName)
                seatsTable = json.loads(activity[0].seat_table)
                ticket = Ticket.objects.select_for_update().filter(status=1, seat=seat)
                other_ticket = Ticket.objects.filter(status=1, seat=other_seat)
                if ticket.exists() or other_ticket.exists():
                    rtnJSON['seat'] = seatsTable
                    rtnJSON['msg'] = 'invalidSeat'
                    return HttpResponse(json.dumps(rtnJSON), content_type='application/json')
                else:
                    seatsTable[row][column] = 2
                    seatsTable[other_row][other_column] = 2
                    seats_list = json.dumps(seatsTable)
                    activity = Activity.objects.filter(name=activityName)
                    Ticket.objects.filter(unique_id=ticketID).update(seat=seat)
                    Ticket.objects.filter(stu_id=other_stu_id, activity=activity[0]).update(seat=other_seat)
                    activity.update(seat_table=seats_list)
                    rtnJSON['seat'] = seatsTable
                    rtnJSON['msg'] = 'success'
                    rtnJSON['next_url'] = s_reverse_ticket_detail(uid)
                    return HttpResponse(json.dumps(rtnJSON), content_type='application/json')
            else:
                activity = Activity.objects.select_for_update().filter(name = activityName)
                seatsTable = json.loads(activity[0].seat_table)
                ticket = Ticket.objects.select_for_update().filter(status=1, seat=seat)
                if ticket.exists():
                    rtnJSON['seat'] = seatsTable
                    rtnJSON['msg'] = 'invalidSeat'
                    return HttpResponse(json.dumps(rtnJSON), content_type='application/json')
                else:
                    seatsTable[row][column] = 2
                    seats_list = json.dumps(seatsTable)
                    Ticket.objects.filter(unique_id=ticketID).update(seat=seat)
                    Activity.objects.filter(name=activityName).update(seat_table=seats_list)
                    rtnJSON['seat'] = seatsTable
                    rtnJSON['msg'] = 'success'
                    rtnJSON['next_url'] = s_reverse_ticket_detail(uid)
                    return HttpResponse(json.dumps(rtnJSON), content_type='application/json')
