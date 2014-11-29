#-*- coding:utf-8 -*-

from django.db.models import F, Q
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
from weixinlib.settings import WEIXIN_APPID

def create_test_users(num):
    for i in range(1, num+1, 1):
        try:
            openid = str(i).rjust(4, '0')
            newuser = User.objects.create(weixin_id=openid, stu_id=str(-i), stu_name=str(i), stu_type=u"本科生", status=1)
            newuser.save()
        except:
            break
    return

create_test_users(3000)