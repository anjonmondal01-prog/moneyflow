from decimal import Decimal
from datetime import time
from rest_framework import serializers
from .models import *
from .engine import FinancialEngine

class AccountSerializer(serializers.ModelSerializer):
    balance=serializers.SerializerMethodField()
    def get_balance(self,obj): return FinancialEngine.account_balance(obj)
    class Meta:
        model=Account
        fields='id name kind opening_balance balance'.split()

class PersonSerializer(serializers.ModelSerializer):
    outstanding_receivable=serializers.SerializerMethodField()
    outstanding_payable=serializers.SerializerMethodField()
    def get_outstanding_receivable(self,o):
        lent=sum((x.amount for x in o.transactions.filter(status='active',type='lend')),Decimal('0'))
        lent+=sum((x.amount for x in o.transactions.filter(status='active',type='help',expected_return=True)),Decimal('0'))
        rep=sum((x.amount for x in o.transactions.filter(status='active',type='repayment_received')),Decimal('0'))
        return lent-rep
    def get_outstanding_payable(self,o):
        borrowed=sum((x.amount for x in o.transactions.filter(status='active',type='borrow')),Decimal('0'))
        rep=sum((x.amount for x in o.transactions.filter(status='active',type='repayment_made')),Decimal('0'))
        return borrowed-rep
    class Meta:
        model=Person
        fields='id name relationship contact notes outstanding_receivable outstanding_payable'.split()

class OwnedRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        qs=super().get_queryset()
        request=self.context.get('request')
        return qs.filter(user=request.user) if request and request.user.is_authenticated else qs.none()

class TransactionSerializer(serializers.ModelSerializer):
    currency=serializers.CharField(read_only=True,required=False)
    type=serializers.ChoiceField(choices=Transaction.TYPES,required=True)
    amount=serializers.DecimalField(max_digits=18,decimal_places=2,required=True)
    date=serializers.DateField(required=False)
    exact_time=serializers.TimeField(required=False)
    category=serializers.CharField(required=False,allow_blank=True,default='Other')
    item=serializers.CharField(required=False,allow_blank=True,default='')
    income_source=serializers.CharField(required=False,allow_blank=True,default='')
    subcategory=serializers.CharField(required=False,allow_blank=True,default='')
    purpose=serializers.CharField(required=False,allow_blank=True,default='')
    reason=serializers.CharField(required=False,allow_blank=True,default='')
    description=serializers.CharField(required=False,allow_blank=True,default='')
    notes=serializers.CharField(required=False,allow_blank=True,default='')
    tags=serializers.JSONField(required=False,default=list)
    quantity=serializers.DecimalField(max_digits=18,decimal_places=3,required=False,allow_null=True)
    unit=serializers.CharField(required=False,allow_blank=True,default='')
    price_per_unit=serializers.DecimalField(max_digits=18,decimal_places=2,required=False,allow_null=True)
    person=OwnedRelatedField(queryset=Person.objects.all(),allow_null=True,required=False)
    account=OwnedRelatedField(queryset=Account.objects.all(),allow_null=True,required=False)
    destination_account=OwnedRelatedField(queryset=Account.objects.all(),allow_null=True,required=False)
    payment_method=serializers.CharField(required=False,allow_blank=True,default='')
    location=serializers.CharField(required=False,allow_blank=True,default='')
    shop_store=serializers.CharField(required=False,allow_blank=True,default='')
    related_transaction=OwnedRelatedField(queryset=Transaction.objects.all(),allow_null=True,required=False)
    due_date=serializers.DateField(required=False,allow_null=True)
    expected_return=serializers.BooleanField(required=False,allow_null=True,default=None)
    status=serializers.CharField(required=False,default='active')

    class Meta:
        model=Transaction
        exclude=('user',)

    def validate(self,data):
        request=self.context['request']
        data['date']=data.get('date') or request.user.date_joined.date()
        data['exact_time']=data.get('exact_time') or time(0,0)
        if data.get('type') in {'income','salary','money_added'} and not data.get('category'):
            data['category']='Other'
        FinancialEngine.validate_mutation(data,request.user,self.instance)
        return data

class BudgetSerializer(serializers.ModelSerializer):
    name=serializers.CharField(required=False,default='Monthly Spending Target')
    period=serializers.CharField(required=False,default='monthly')
    amount=serializers.DecimalField(max_digits=18,decimal_places=2,required=True)
    category=serializers.CharField(required=False,allow_blank=True,default='')
    start_date=serializers.DateField(required=True)
    end_date=serializers.DateField(required=True)
    active=serializers.BooleanField(required=False,default=True)
    used=serializers.SerializerMethodField()
    remaining=serializers.SerializerMethodField()
    percentage=serializers.SerializerMethodField()
    def _used(self,o):
        from django.db.models import Sum
        q=Transaction.objects.filter(user=o.user,status='active',type='expense',date__range=(o.start_date,o.end_date))
        q=q.filter(category=o.category) if o.category else q
        return q.aggregate(v=Sum('amount'))['v'] or Decimal('0')
    def get_used(self,o): return self._used(o)
    def get_remaining(self,o): return o.amount-self._used(o)
    def get_percentage(self,o): return round(float(self._used(o)/o.amount*100),2) if o.amount else 0
    class Meta:
        model=Budget
        fields='id name amount period category start_date end_date active used remaining percentage'.split()

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model=Goal
        fields='id name target_amount current_amount target_date'.split()

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model=Reminder
        fields='id title due_at kind done'.split()
