from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
                       url(r'^$', 'userpage.views.home'),
                       url(r'^validate/try/$', 'userpage.views.validate_post'),
                       url(r'^validate/try_auth/$', 'userpage.views.validate_post_auth'),
                       url(r'^validate/time_auth/$', 'userpage.views.validate_get_time_auth'),
                       url(r'^validate/(?P<openid>\S+)/$', 'userpage.views.validate_view'),
                       url(r'^activity/(?P<activityid>\d+)/$','userpage.views.details_view'),
                       url(r'^ticket/(?P<uid>\S+)/$','userpage.views.ticket_view'),
                       url(r'^help/$','userpage.views.help_view'),
                       url(r'^helpact/$','userpage.views.helpact_view'),
                       url(r'^helpclub/$','userpage.views.helpclub_view'),
                       url(r'^helplecture/$','userpage.views.helplecture_view'),
                       url(r'^activity/(?P<actid>\d+)/menu/$', 'userpage.views.activity_menu_view'),
                       url(r'^ticket/(?P<weixinid>\S+)$', uc_ticket),
                       url(r'^account/(?P<weixinid>\S+)$', uc_account),
                       url(r'^couple/(?P<weixinid>\S+)$', uc_2ticket),
                       url(r'^token/(?P<weixinid>\S+)$', uc_token),
                       url(r'^seat/(?P<uid>\S+)/$', 'userpage.views.views_seats'),
                       )

