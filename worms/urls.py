from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^worm-strains/$', views.worms, name='worms_url'),
    url(r'^add-strain/$', views.add_strain, name='add_strain_url'),
]
