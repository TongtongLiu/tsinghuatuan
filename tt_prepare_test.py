#-*- coding:utf-8 -*-

from django.contrib import auth
from django.contrib.auth.models import User

def create_test_users(num):
    for i in range(1, num+1):
        try:
            newuser = User.objects.create(weixin_id=str(i).rjust(4, '0'), stu_id=str(-i), stu_name=str(i), stu_type=u"本科生", status=1)
            newuser.save()
        except:
            break;
    return

create_test_users(3000)