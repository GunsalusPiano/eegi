from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'},
        name='login_url'),
    url(r'^logout/$', auth_views.logout, name='logout_url'),
    url(r'^', include('website.urls')),
    url(r'^', include('worms.urls')),
    url(r'^', include('clones.urls')),
    url(r'^', include('library.urls')),
    url(r'^', include('experiments.urls')),
]

if settings.DEBUG == True:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
