#-*- coding:utf-8 -*-

__author__ = 'liutongtong'

from urlhandler.models import User

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