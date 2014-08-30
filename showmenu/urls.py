from django.conf.urls import patterns, url, include

from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('cms.urls')),
    url(r'^', include(admin.site.urls)),
) + staticfiles_urlpatterns()
