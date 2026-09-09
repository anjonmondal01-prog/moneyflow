from django.contrib import admin
from .models import *
for m in [User,Account,Person,Transaction,AuditEvent,Budget,Goal,Reminder]: admin.site.register(m)
