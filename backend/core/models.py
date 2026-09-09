from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email=models.EmailField(unique=True)
    currency=models.CharField(max_length=8,default='BDT')
    USERNAME_FIELD='email'; REQUIRED_FIELDS=['username']

class Account(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='accounts')
    name=models.CharField(max_length=120); kind=models.CharField(max_length=40,default='cash')
    opening_balance=models.DecimalField(max_digits=18,decimal_places=2,default=Decimal('0')); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=('user','name')

class Person(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='people'); name=models.CharField(max_length=160)
    relationship=models.CharField(max_length=120,blank=True); contact=models.CharField(max_length=120,blank=True); notes=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    TYPES=[('expense','Expense'),('income','Income'),('salary','Salary'),('money_added','Money Added'),('lend','Lending'),('borrow','Borrowing'),('help','Helping'),('repayment_received','Repayment Received'),('repayment_made','Repayment Made'),('transfer','Transfer')]
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='transactions'); type=models.CharField(max_length=32,choices=TYPES); amount=models.DecimalField(max_digits=18,decimal_places=2); currency=models.CharField(max_length=8)
    date=models.DateField(); exact_time=models.TimeField(); item=models.CharField(max_length=200,blank=True); income_source=models.CharField(max_length=200,blank=True); category=models.CharField(max_length=120,blank=True); subcategory=models.CharField(max_length=120,blank=True); purpose=models.CharField(max_length=200,blank=True); reason=models.CharField(max_length=200,blank=True); description=models.TextField(blank=True); notes=models.TextField(blank=True); tags=models.JSONField(default=list,blank=True)
    quantity=models.DecimalField(max_digits=18,decimal_places=3,null=True,blank=True); unit=models.CharField(max_length=40,blank=True); price_per_unit=models.DecimalField(max_digits=18,decimal_places=2,null=True,blank=True)
    person=models.ForeignKey(Person,on_delete=models.SET_NULL,null=True,blank=True,related_name='transactions'); account=models.ForeignKey(Account,on_delete=models.SET_NULL,null=True,blank=True,related_name='transactions'); destination_account=models.ForeignKey(Account,on_delete=models.SET_NULL,null=True,blank=True,related_name='incoming_transfers')
    payment_method=models.CharField(max_length=80,blank=True); location=models.CharField(max_length=180,blank=True); shop_store=models.CharField(max_length=180,blank=True); related_transaction=models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='related_repayments'); due_date=models.DateField(null=True,blank=True); expected_return=models.BooleanField(null=True,blank=True); status=models.CharField(max_length=24,default='active'); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: indexes=[models.Index(fields=['user','date']),models.Index(fields=['user','type']),models.Index(fields=['user','status'])]

class AuditEvent(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='audit_events'); entity_type=models.CharField(max_length=80); entity_id=models.BigIntegerField(); action=models.CharField(max_length=40); timestamp=models.DateTimeField(auto_now_add=True); previous_state=models.JSONField(null=True,blank=True); new_state=models.JSONField(null=True,blank=True)
class Budget(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='budgets'); name=models.CharField(max_length=140); amount=models.DecimalField(max_digits=18,decimal_places=2); period=models.CharField(max_length=20,default='monthly'); category=models.CharField(max_length=120,blank=True); start_date=models.DateField(); end_date=models.DateField(); active=models.BooleanField(default=True)
class Goal(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='goals'); name=models.CharField(max_length=160); target_amount=models.DecimalField(max_digits=18,decimal_places=2); current_amount=models.DecimalField(max_digits=18,decimal_places=2,default=Decimal('0')); target_date=models.DateField(null=True,blank=True)
class Reminder(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='reminders'); title=models.CharField(max_length=180); due_at=models.DateTimeField(); kind=models.CharField(max_length=40,default='custom'); done=models.BooleanField(default=False)
