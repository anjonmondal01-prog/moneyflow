from decimal import Decimal
from django.db.models import Q, Sum
from .models import Transaction, Account

IN={'income','salary','money_added','borrow','repayment_received'}
OUT={'expense','lend','help','repayment_made'}

class FinancialEngine:
    @staticmethod
    def active_qs(user):
        return Transaction.objects.filter(user=user,status='active')

    @classmethod
    def account_balance(cls,account):
        if not account:
            return Decimal('0')
        total=account.opening_balance
        for t in cls.active_qs(account.user).filter(Q(account=account)|Q(destination_account=account)):
            if t.type=='transfer':
                if t.account_id==account.id:
                    total-=t.amount
                if t.destination_account_id==account.id:
                    total+=t.amount
            elif t.account_id==account.id:
                total += t.amount if t.type in IN else -t.amount
        return total

    @classmethod
    def summary(cls,user):
        qs=cls.active_qs(user)
        z=Decimal('0')
        def s(types):
            return qs.filter(type__in=list(types)).aggregate(v=Sum('amount'))['v'] or z
        received=s(IN)
        spent=s(OUT)
        lending=s({'lend'})
        borrowing=s({'borrow'})
        helping=s({'help'})
        rr=s({'repayment_received'})
        rm=s({'repayment_made'})
        account_opening=sum((a.opening_balance for a in Account.objects.filter(user=user)),z)
        balance=account_opening + received - spent
        expected=qs.filter(type='help',expected_return=True).aggregate(v=Sum('amount'))['v'] or z
        return {
            'available_balance':balance,
            'money_received':received,
            'money_spent':spent,
            'money_lent':lending,
            'money_borrowed':borrowing,
            'helping':helping,
            'repayments_received':rr,
            'repayments_made':rm,
            'receivable':lending+expected-rr,
            'payable':borrowing-rm,
        }

    @staticmethod
    def validate_mutation(data,user,instance=None):
        from django.core.exceptions import ValidationError
        amount=Decimal(str(data.get('amount',getattr(instance,'amount',0))))
        if amount<=0:
            raise ValidationError('Amount must be greater than 0.')
        typ=data.get('type',getattr(instance,'type',None))
        account=data.get('account',getattr(instance,'account_id',None))
        destination=data.get('destination_account',getattr(instance,'destination_account_id',None))
        person=data.get('person',getattr(instance,'person_id',None))
        if typ=='transfer':
            if not account or not destination:
                raise ValidationError('Select both source and destination accounts for a transfer.')
            if str(account)==str(destination):
                raise ValidationError('Choose two different accounts.')
        if typ in {'lend','help','borrow','repayment_received','repayment_made'} and not person:
            raise ValidationError('Select a person for this transaction.')
        if typ=='help' and data.get('expected_return') is True and not person:
            raise ValidationError('Helping marked as repayable requires a person.')
