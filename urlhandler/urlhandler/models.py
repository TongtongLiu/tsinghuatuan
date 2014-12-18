#-*- coding: UTF-8 -*-
from django.db import models


class User(models.Model):
    weixin_id = models.CharField(max_length=255)
    stuid = models.CharField(max_length=255)
    stu_name = models.CharField(max_length=255)
    stu_type = models.CharField(max_length=255)
    bind_count = models.IntegerField(default=0)
    status = models.IntegerField()
    seed = models.FloatField(default=1024)


class Activity(models.Model):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    place = models.CharField(max_length=255)
    book_start = models.DateTimeField()
    book_end = models.DateTimeField()
    seat_status = models.IntegerField(default=0)
    seat_table = models.CharField(max_length=1024)
    total_tickets = models.IntegerField()
    status = models.IntegerField()
    pic_url = models.CharField(max_length=255)
    remain_tickets = models.IntegerField()
    menu_url = models.CharField(max_length=255, null=True)
    seat_price = models.CharField(max_length=255)
    # Something about status:
    # -1: deleted
    # 0: saved but not published
    # 1: published
    # Something about seat_status:
    # 0: no seat
    # 1: seat B and seat C
    # 2: select seat


class Ticket(models.Model):
    stuid = models.CharField(max_length=255)
    unique_id = models.CharField(max_length=255)
    activity = models.ForeignKey(Activity)
    status = models.IntegerField()
    partner_id = models.CharField(max_length=255)
    seat = models.CharField(max_length=255)
    # Something about isUsed
    # 0: ticket order is cancelled
    # 1: ticket order is valid
    # 2: ticket is used


class Bind(models.Model):
    activity = models.ForeignKey(Activity)
    active_stuid = models.CharField(max_length=255)
    passive_stuid = models.CharField(max_length=255)
    unique_id = models.CharField(max_length=255)


class Seat(models.Model):
    position_row = models.IntegerField()
    position_column = models.IntegerField()
    seat_section = models.CharField(max_length=255)
    price = models.IntegerField()
    is_selected = models.IntegerField()
    activity = models.ForeignKey(Activity)
    

'''
class UserSession(models.Model):
    stuid = models.CharField(max_length=255)
    session_key = models.CharField(max_length=255)
    session_status = models.IntegerField(1)

    def generate_session(self,stuid):
        try:
            stu = User.objects.get(stuid=stuid)
            sessions = UserSession.objects.filter(stuid = stuid)
            if sessions:
                for session in sessions:
                    session.delete()
            s = UserSession(stuid=stuid,session_key=uuid.uuid4(),session_status = 0)
            s.save()
            return True
        except:
            return False

    def is_session_valid(self,stuid,session_key):
        try:
            s = UserSession.objects.get(stuid=stuid,session_key=session_key)
            if(s.session_status == 0):
                s.session_status = 1
                s.save()
                return True
            else:
                s.delete()
                return False
        except:
            return False

    def can_print(self,stuid,session_key):
        try:
            s = UserSession.objects.get(stuid=stuid,session_key=session_key)
            return True
        except:
            return False
'''
