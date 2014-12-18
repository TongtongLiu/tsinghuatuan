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
from urlhandler.models import User, Activity, Ticket, Bind, Seat
from userpage.safe_reverse import *
from weixinlib import http_get
from weixinlib.settings import WEIXIN_OAUTH2_URL
from weixinlib.weixin_urls import WEIXIN_URLS


TIMESTAMP_URL = "http://auth.igeek.asia/v1/time"
VALIDATION_URL = "http://auth.igeek.asia/v1"


def disable_users(users):
    users.update(status=0)


def insert_user(openid, stu_id, stu_name, stu_type):
    new_user = User.objects.create(weixin_id=openid, stu_id=stu_id,
                                   stu_name=stu_name, stu_type=stu_type,
                                   status=1)
    new_user.save()


def select_users_by_openid(openid):
    return User.objects.filter(weixin_id=openid, status=1)


def select_users_by_stu_id(stu_id):
    return User.objects.filter(stu_id=stu_id, status=1)


def update_user_by_stu_id(stu_id, openid, stu_name, stu_type):
    user = User.objects.filter(stu_id=stu_id)[0]
    user.weixin_id = openid
    user.stu_name = stu_name
    user.stu_type = stu_type
    user.status = 1
    user.bind_count = 0
    user.save()


def select_activities_by_id(activity_id):
    return Activity.objects.filter(id=activity_id)


def select_activities_by_name(activity_name):
    return Activity.objects.filter(name=activity_name, status=1)


def select_activities_valid():
    now = datetime.datetime.now()
    return Activity.objects.filter(status=1, end_time__gt=now, book_start__lt=now)


def update_activity_seat_table(activity, seat_table):
    activity.seat_table = seat_table
    activity.save()


def update_activity_tickets(activity, remain_tickets):
    activity.remain_tickets = remain_tickets
    activity.save()


def disable_tickets(tickets):
    tickets.update(status=0)


def select_tickets_by_id(unique_id):
    return Ticket.objects.filter(unique_id=unique_id)


def select_tickets_unused_by_stu_id(stu_id):
    return Ticket.objects.filter(stu_id=stu_id, status=1)


def select_tickets_by_stu_id_and_activity(stu_id, activity):
    return Ticket.objects.filter(stu_id=stu_id, activity=activity, status__gt=0)


def delete_binds(binds):
    User.objects.filter(stu_id=binds[0].active_stu_id, status=1).update(bind_count=F('bind_count')-1)
    User.objects.filter(stu_id=binds[0].passive_stu_id, status=1).update(bind_count=F('bind_count')-1)
    binds.delete()


def delete_binds_of_user(user):
    binds1 = Bind.objects.filter(active_stu_id=user.stu_id)
    for bind in binds1:
        bind_count = user.bind_count - 1
        user.bind_count = bind_count
        user.save()
        User.objects.filter(stu_id=bind.passive_stu_id, status=1).update(bind_count=F('bind_count')-1)
    binds1.delete()
    binds2 = Bind.objects.filter(passive_stu_id=user.stu_id)
    for bind in binds2:
        bind_count = user.bind_count - 1
        user.bind_count = bind_count
        user.save()
        User.objects.filter(stu_id=bind.active_stu_id, status=1).update(bind_count=F('bind_count')-1)
    binds2.delete()


def insert_bind(activity, active_stu_id, passive_stu_id, unique_id):
    new_bind = Bind.objects.create(activity=activity,
                                   active_stu_id=active_stu_id,
                                   passive_stu_id=passive_stu_id,
                                   unique_id=unique_id)
    new_bind.save()
    User.objects.filter(stu_id=active_stu_id, status=1).update(bind_count=F('bind_count')+1)
    User.objects.filter(stu_id=passive_stu_id, status=1).update(bind_count=F('bind_count')+1)


def select_binds_by_id(unique_id):
    return Bind.objects.filter(unique_id=unique_id)


def select_binds_by_stu_id(stu_id):
    return Bind.objects.filter(Q(active_stu_id=stu_id) | Q(passive_stu_id=stu_id))


def select_binds_by_active_stu_id_and_activity(active_stu_id, activity):
    return Bind.objects.filter(active_stu_id=active_stu_id, activity=activity)


def select_binds_by_passive_stu_id_and_activity(passive_stu_id, activity):
    return Bind.objects.filter(passive_stu_id=passive_stu_id, activity=activity)


def home(request):
    return render_to_response('mobile_base.html')


def validate_view(request, openid):
    if select_users_by_openid(openid).exists():
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
    request_url = TIMESTAMP_URL
    req = urllib2.Request(url=request_url)
    res_data = urllib2.urlopen(req)
    try:
        res = res_data.read()
    except IOError:
        return HttpResponse('Error')
    return HttpResponse(res)


def validate_through_auth(secret):
    req_data = urllib.urlencode({'secret': secret})
    request_url = VALIDATION_URL
    req = urllib2.Request(url=request_url, data=req_data)
    res_data = urllib2.urlopen(req)
    try:
        res = res_data.read()
    except IOError:
        return {'result': 'Error'}
    res_dict = json.loads(res)
    if res_dict['code'] == 0:
        return {
            'result': 'Accepted',
            'name': res_dict['data']['name'],
            'type': res_dict['data']['usertype']
        }
    else:
        return {'result': 'Rejected'}


def uc_validate_post_auth(request):
    if ((not request.POST) or
            (not 'openid' in request.POST) or
            (not 'username' in request.POST) or
            (not 'password' in request.POST)):
        raise Http404
    openid = request.POST['openid']
    stu_id = request.POST['username']
    if not stu_id.isdigit():
        raise Http404
    secret = request.POST['password']
    validate_result = validate_through_auth(secret)
    if validate_result['result'] == 'Accepted':
        if not validate_result['type']:
            validate_result['type'] = u'教师'
        try:
            disable_users(select_users_by_openid(openid))
            disable_users(select_users_by_stu_id(stu_id))
        except IOError:
            return HttpResponse('Error')
        try:
            update_user_by_stu_id(stu_id, openid,
                                  validate_result['name'], 
                                  validate_result['type'])
        except IOError:
            try:
                insert_user(openid, stu_id,
                            validate_result['name'],
                            validate_result['type'])
            except IOError:
                return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_account(openid))
    return HttpResponse(validate_result['result'])


###################### Activity Detail ######################

STRING_MAX_LEN = 256


def details_view(request, activity_id):
    activities = select_activities_by_id(activity_id)
    if not activities.exists():
        raise Http404    # current activity is invalid
    act_name = activities[0].name
    act_key = activities[0].key
    act_place = activities[0].place
    act_book_start = activities[0].book_start
    act_book_end = activities[0].book_end
    act_begin_time = activities[0].start_time
    act_end_time = activities[0].end_time
    act_total_tickets = activities[0].total_tickets
    act_text = activities[0].description
    act_ticket_remain = activities[0].remain_tickets
    act_abstract = act_text
    act_text_status = 0
    if len(act_text) > STRING_MAX_LEN:
        act_text_status = 1
        act_abstract = act_text[0:STRING_MAX_LEN] + u'...'
    act_photo = activities[0].pic_url
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
    variables = RequestContext(request, {
        'act_name': act_name,
        ' act_text': act_text,
        'act_photo': act_photo,
        'act_book_start': act_book_start,
        'act_book_end': act_book_end,
        'act_begin_time': act_begin_time,
        'act_end_time': act_end_time,
        'act_totaltickets': act_total_tickets,
        'act_key': act_key,
        'act_place': act_place,
        'act_status': act_status,
        'act_seconds': act_seconds,
        'cur_time': cur_time,
        'act_abstract': act_abstract,
        'act_text_status': act_text_status,
        'act_ticket_remain': act_ticket_remain
    })
    return render_to_response('activitydetails.html', variables)


def ticket_view(request, uid):
    tickets = select_tickets_by_id(uid)
    if not tickets.exists() or tickets[0].status == 0:
        information = u'该票无效'
        href = WEIXIN_OAUTH2_URL
        return render_to_response('404.html', {
            'information': information,
            'href': href
        })  # current activity is invalid
    activities = select_activities_by_id(tickets[0].activity_id)
    act_id = activities[0].id
    act_name = activities[0].name
    act_key = activities[0].key
    act_begin_time = activities[0].start_time
    act_end_time = activities[0].end_time
    act_place = activities[0].place
    ticket_status = tickets[0].status
    now = datetime.datetime.now()
    if act_end_time < now:  # 表示活动已经结束
        ticket_status = 3
    ticket_seat = tickets[0].seat
    if activities[0].seat_status == 1:
        ticket_url = s_reverse_ticket_select_zongti(uid)
    else:
        ticket_url = s_reverse_ticket_selection(uid)
    act_photo = '{}/fit/{}'.format(QRCODE_URL, uid)
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


def activity_menu_view(request, activity_id):
    activities = select_activities_by_id(activity_id)
    return render_to_response('activitymenu.html', {'activity': activities[0]})


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
    rtn_json = json.loads(res)
    openid = rtn_json['openid']
    if select_users_by_openid(openid).exists():
        return redirect(s_reverse_uc_ticket(openid))
    else:
        return redirect(s_reverse_uc_account(openid))


def uc_account(request, openid):
    users = select_users_by_openid(openid)
    if users:
        if request.method == 'POST':
            try:
                delete_binds_of_user(users[0])
                disable_users(users)
            except IOError:
                return HttpResponse('logout error')
            return render_to_response('usercenter_account_login.html',
                                      {'weixin_id': openid},
                                      context_instance=RequestContext(request))
        else:
            return render_to_response('usercenter_account.html', {
                'weixin_id': openid,
                'student_id': users[0].stu_id,
                'student_name': users[0].stu_name,
                'student_type': users[0].stu_type
            }, context_instance=RequestContext(request))
    else:
        return render_to_response('usercenter_account_login.html',
                                  {'weixin_id': openid},
                                  context_instance=RequestContext(request))


@csrf_exempt
def uc_ticket(request, openid):
    if request.method == 'POST':
        if request.POST.get('ticket_uid', ''):
            ticket_uid = request.POST['ticket_uid']
            ticket_url = s_reverse_ticket_detail(ticket_uid)
            seat_url = s_reverse_ticket_selection(ticket_uid)
            rtn_json = {'ticketURL': ticket_url, 'seatURL': seat_url}
            return HttpResponse(json.dumps(rtn_json),
                                content_type='application/json')
    if request.is_ajax():
        if not request.POST.get('ticket_id', ''):
            return HttpResponse('logout error')
        else:
            unique_id = request.POST['ticket_id']
            tickets = select_tickets_by_id(unique_id)
            if not tickets.exists():
                return HttpResponse('logout error')
            else:
                ticket = tickets[0]
                disable_tickets(tickets)
                seat = ticket.seat.split('-')
                activity = ticket.activity
                if len(seat) > 1:
                    row = int(seat[0]) - 1
                    column = int(seat[1]) - 1
                    seat_table = json.loads(activity.seat_table)
                    seat_table[row][column] = 1
                    update_activity_seat_table(activity, json.dumps(json.dumps(seat_table)))
                update_activity_tickets(activity, activity.remain_tickets + 1)
            return HttpResponse('logout error')
    tickets = []
    users = select_users_by_openid(openid)
    if users:
        is_validated = 1
        tickets = select_tickets_unused_by_stu_id(users[0].stu_id)
    else:
        is_validated = 0
    return render_to_response('usercenter_ticket.html', {
        'tickets': tickets,
        'isValidated': is_validated,
        'weixin_id': openid})


def encode_token(openid):
    users = select_users_by_openid(openid)
    timestamp = int(time.time()) / 100
    token = int(users[0].stu_id) ^ timestamp
    return token


def decode_token(token):
    if not token.isdigit():
        return '-1'
    timestamp = int(time.time()) / 100
    stu_id = str(int(token) ^ timestamp)
    return stu_id


def uc_2ticket_bind(request):
    if ((not request.POST) or
            (not 'openid' in request.POST) or
            (not 'activity_name' in request.POST) or
            (not 'token' in request.POST)):
        raise Http404
    openid = request.POST['openid']
    users = select_users_by_openid(openid)
    if not users:
        raise Http404
    active_stu_id = users[0].stu_id
    activities = select_activities_by_name(request.POST['activity_name'])
    if not activities:
        raise Http404
    passive_stu_id = decode_token(request.POST['token'])
    if active_stu_id == passive_stu_id:
        return HttpResponse('SameStudentID')
    if not select_users_by_stu_id(passive_stu_id).exists():
        return HttpResponse('TokenError')
    if select_tickets_by_stu_id_and_activity(passive_stu_id, activities[0]).exists():
        return HttpResponse('HaveTicket')
    if (select_binds_by_active_stu_id_and_activity(passive_stu_id, activities[0]).exists() or
            select_binds_by_passive_stu_id_and_activity(passive_stu_id, activities[0]).exists()):
        return HttpResponse('AlreadyBinded')
    else:
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        while select_binds_by_id(random_string).exists():
            random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        try:
            insert_bind(activities[0], active_stu_id, passive_stu_id, random_string)
        except IOError:
            return HttpResponse('Error')
        return HttpResponse(s_reverse_uc_2ticket(openid))


@csrf_exempt
def uc_2ticket(request, openid):
    if request.is_ajax():
        try:
            delete_binds(select_binds_by_id(request.POST['unique_id']))
            return HttpResponse('Success')
        except IOError:
            return HttpResponse('Error')
    else:
        users = select_users_by_openid(openid)
        if users:
            is_validated = 1
            binds = select_binds_by_stu_id(users[0].stu_id)
            tickets = select_tickets_unused_by_stu_id(users[0].stu_id)
            activity_valid = select_activities_valid()
            return render_to_response('usercenter_2ticket.html', {
                'isValidated': is_validated,
                'weixin_id': openid,
                'stu_id': users[0].stu_id,
                'activity_valid': activity_valid,
                'binds': binds,
                'tickets': tickets,
                'binds_info': 123,
                'binds_info_len': 123
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
        if select_users_by_openid(openid).exists():
            is_validated = 1
        else:
            is_validated = 0
        return render_to_response('usercenter_token.html',
                                  {'isValidated': is_validated, 'weixin_id': openid})


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


@csrf_exempt
def select_seats_xinqing_post(request):
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
            return_json['msg'] = 'error'
        else:
            return_json['msg'] = 'success'
            return_json['next_url'] = s_reverse_ticket_detail(post['ticket_id'])
        return HttpResponse(json.dumps(return_json), content_type='application/json')
    except Exception:
        return HttpResponse(json.dumps(return_json), content_type='application/json')


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
        print seats_selected
        seat_1 = seats_selected[0].split('-')
        print seat_1
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
        if len(seats_selected) >= 2:
            try:
                partner_ticket = Ticket.objects.get(stu_id=ticket.partner_id,
                                                    activity=ticket.activity)
            except Exception:
                return None
            seat_2 = seats_selected[1].split('-')
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
                return None
            seat = seat_2_db[0]
            seat.save()
            partner_ticket.seat = seats_selected[1]
            partner_ticket.save()
            change_seat_status(activity, row_2, column_2, 2)
        seat = seat_1_db[0]
        seat.is_selected = 1
        seat.save()
        ticket.seat = seats_selected[0]
        ticket.save()
        change_seat_status(activity, row_1, column_1, 2)
        return seat

def change_seat_status(activity, row, column, status):
    seat_table = json.loads(activity.seat_table)
    seat_table[row][column] = status
    activity.seat_table = json.dumps(seat_table)
    activity.save()