# -*- coding: utf-8 -*-
from .base import *
import dj_database_url
import os

DEBUG = False

DATABASES = {
    'default': dj_database_url.config()
}


DATABASES['default']['ENGINE'] = 'django_postgrespool'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = ['*']
