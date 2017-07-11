from django.conf.urls import url
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    url(r'^clones/$', views.clones, name='clones_url'),
    url(r'^clone/([^/]*)/$', views.clone, name='clone_url'),
    url(r'^descriptions/$', views.descriptions , name='descriptions_url'),
]
