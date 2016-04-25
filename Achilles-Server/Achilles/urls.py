"""Achilles URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from Heal import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^admin/', include(admin.site.urls)),
]

__actions = ['config', 'start', 'stop', 'result']
urlpatterns.extend(
    [url('^' + action + '/$',
         getattr(views, action),
         name=action)
     for action in __actions])
