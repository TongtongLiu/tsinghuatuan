from django.core.urlresolvers import reverse
from queryhandler.settings import SITE_DOMAIN


def s_reverse_validate(openid):
    return SITE_DOMAIN + reverse('userpage.views.uc_account', kwargs={'openid': openid})


def s_reverse_activity_detail(activityid):
    return SITE_DOMAIN + reverse('userpage.views.details_view', kwargs={'activityid': activityid})


def s_reverse_ticket_detail(uid):
    return SITE_DOMAIN + reverse('userpage.views.ticket_view', kwargs={'uid': uid})


def s_reverse_help():
    return SITE_DOMAIN + reverse('userpage.views.help_view')


def s_reverse_activity_menu(actid):
    return SITE_DOMAIN + reverse('userpage.views.activity_menu_view', kwargs={'actid': actid})


def s_reverse_uc_ticket(openid):
    return SITE_DOMAIN + reverse('userpage.views.uc_ticket', kwargs={'openid': openid})


def s_reverse_uc_account(openid):
    return SITE_DOMAIN + reverse('userpage.views.uc_account', kwargs={'openid': openid})


def s_reverse_uc_2ticket(openid):
    return SITE_DOMAIN + reverse('userpage.views.uc_2ticket', kwargs={'openid': openid})


def s_reverse_ticket_selection(uid):
    return SITE_DOMAIN + reverse('userpage.views.views_seats', kwargs={'uid': uid})
