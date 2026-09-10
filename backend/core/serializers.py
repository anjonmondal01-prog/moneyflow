from rest_framework import serializers
from .models import *
from .engine import FinancialEngine

class AccountSerializer(serializers.ModelSerializer):
    balance=serializers.SerializerMethodField()
    def get_balance(self,obj): return FinancialEngine.account_balance(obj)
    class Meta: model=Account; fields='id name kind opening_balance balance'.split()

class PersonSerializer(serializers.ModelSerializer):
    outstanding_receivable=serializers.SerializerMethodField(); outstanding_payable=serializers.SerializerMethodField()
    def get_outstanding_receivable(self,o):
        lent=sum((x.amount for x in o.transactions.filter(status='active',type='lend')),start=0)+sum((x.amount for x in o.transactions.filter(status='active',type='help',expected_return=True)),start=0)
        rep=sum((x.amount for x in o.transactions.filter(status='active',type='repayment_received')),start=0)
        return lent-rep
    def get_outstanding_payable(self,o):
        borrowed=sum((x.amount for x in o.transactions.filter(status='active',type='borrow')),start=0)
        rep=sum((x.amount for x in o.transactions.filter(status='active',type='repayment_made')),start=0)
        return borrowed-rep
    class Meta: model=Person; fields='id name relationship contact notes outstanding_receivable outstanding_payable'.split()

class OwnedRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        qs=super().get_queryset()
        request=self.context.get('request')
        return qs.filter(user=request.user) if request and request.user.is_authenticated else qs.none()

class TransactionSerializer(serializers.ModelSerializer):
    person=OwnedRelatedField(queryset=Person.objects.all(),allow_null=True,required=False)
    account=OwnedRelatedField(queryset=Account.objects.all(),allow_null=True,required=False)
    destination_account=OwnedRelatedField(queryset=Account.objects.all(),allow_null=True,required=False)
    related_transaction=OwnedRelatedField(queryset=Transaction.objects.all(),allow_null=True,required=False)
    class Meta: model=Transaction; exclude=('user',)
    def validate(self,data):
        FinancialEngine.validate_mutation(data,self.context['request'].user,self.instance)
        return data

class BudgetSerializer(serializers.ModelSerializer):
    used=serializers.SerializerMethodField(); remaining=serializers.SerializerMethodField(); percentage=serializers.SerializerMethodField()
    def _used(self,o):
        from django.db.models import Sum
        q=Transaction.objects.filter(user=o.user,status='active',type='expense',date__range=(o.start_date,o.end_date)); q=q.filter(category=o.category) if o.category else q; return q.aggregate(v=Sum('amount'))['v'] or 0
    def get_used(self,o): return self._used(o)
    def get_remaining(self,o): return o.amount-self._used(o)
    def get_percentage(self,o): return round(float(self._used(o)/o.amount*100),2) if o.amount else 0
    class Meta: model=Budget; fields='id name amount period category start_date end_date active used remaining percentage'.split()
class GoalSerializer(serializers.ModelSerializer):
    class Meta: model=Goal; fields='id name target_amount current_amount target_date'.split()
class ReminderSerializer(serializers.ModelSerializer):
    class Meta: model=Reminder; fields='id title due_at kind done'.split()
