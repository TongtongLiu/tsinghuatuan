from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
                       url(r'^$', 'userpage.views.home'),
                       url(r'^validate/try/$', 'userpage.views.validate_post'),
                       url(r'^validate/try_auth/$', 'userpage.views.validate_post_auth'),
                       url(r'^validate/uc_try_auth/$', 'userpage.views.uc_validate_post_auth'),
                       url(r'^validate/time_auth/$', 'userpage.views.validate_get_time_auth'),
                       url(r'^validate/(?P<openid>\S+)/$', 'userpage.views.validate_view'),
                       url(r'^activity/(?P<activityid>\d+)/$','userpage.views.details_view'),
                       url(r'^ticket/(?P<uid>\S+)/$','userpage.views.ticket_view'),
                       url(r'^help/$','userpage.views.help_view'),
                       url(r'^helpact/$','userpage.views.helpact_view'),
                       url(r'^helpclub/$','userpage.views.helpclub_view'),
                       url(r'^helplecture/$','userpage.views.helplecture_view'),
                       url(r'^activity/(?P<actid>\d+)/menu/$', 'userpage.views.activity_menu_view'),
                       url(r'^uc_center*$', 'userpage.views.uc_center'),
                       url(r'^uc_ticket/(?P<openid>\S+)$', 'userpage.views.uc_ticket'),
                       url(r'^uc_account/(?P<openid>\S+)$', 'userpage.views.uc_account'),
                       url(r'^uc_2ticket/try/$', 'userpage.views.uc_2ticket_bind'),
                       url(r'^uc_2ticket/(?P<openid>\S+)$', 'userpage.views.uc_2ticket'),
                       url(r'^uc_token/(?P<openid>\S+)$', 'userpage.views.uc_token'),
                       url(r'^seat/(?P<uid>\S+)/$', 'userpage.views.views_seats'),
                       url(r'^seats_zongti/(?P<uid>\S+)/$', 'userpage.views.views_seats_zongti'),
                       url(r'^seats_zongti_post/$', 'userpage.views.views_seats_zongti_post'),
                       )

