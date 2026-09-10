from pathlib import Path
import os
from urllib.parse import urlparse
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','dev-only-change-me')
DEBUG=os.getenv('DJANGO_DEBUG','0')=='1'
ALLOWED_HOSTS=[h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost').split(',') if h.strip()]
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','core']
MIDDLEWARE=['corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware']
ROOT_URLCONF='moneyflow.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='moneyflow.wsgi.application'
DATABASE_URL=os.getenv('DATABASE_URL','')
if DATABASE_URL:
    p=urlparse(DATABASE_URL)
    DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':p.path.lstrip('/'),'USER':p.username,'PASSWORD':p.password,'HOST':p.hostname,'PORT':p.port or 5432,'CONN_MAX_AGE':60}}
else:
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE='en-us'
TIME_ZONE=os.getenv('TIME_ZONE','Asia/Dhaka')
USE_I18N=True
USE_TZ=True
STATIC_URL='static/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
AUTH_USER_MODEL='core.User'
CORS_ALLOWED_ORIGINS=[x.strip() for x in os.getenv('CORS_ALLOWED_ORIGINS','http://localhost:5173').split(',') if x.strip()]
CORS_ALLOW_CREDENTIALS=True
CSRF_TRUSTED_ORIGINS=[x.strip() for x in os.getenv('CSRF_TRUSTED_ORIGINS','http://localhost:5173').split(',') if x.strip()]
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SESSION_COOKIE_SAMESITE='Lax'
CSRF_COOKIE_SAMESITE='Lax'
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework.authentication.SessionAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated']}
