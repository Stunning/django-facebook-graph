from django.conf.urls.defaults import *

from views import login, logout, connect

urlpatterns = patterns('',
                       url(r'^login/$', 
                           login,
                           {'template_name': 'registration/login.html'},
                           name='auth_login'),
                       url(r'^logout/$',
                           logout,
                           {'template_name': 'registration/logout.html'},
                           name='auth_logout'),
                       url(r'^connect/$',
                           connect, {},
                           name='fb_connect'),
                       (r'', include('registration.backends.default.urls')),
                       )