"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.views.decorators.cache import never_cache
import os

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Добавляем маршрут для статики
# Всегда добавляем маршрут для статики, чтобы она работала и в DEBUG, и в production
urlpatterns += [
    re_path(
        r'^static/(?P<path>.*)$',
        never_cache(serve),
        {'document_root': str(settings.STATIC_ROOT), 'show_indexes': False}
    ),
]
