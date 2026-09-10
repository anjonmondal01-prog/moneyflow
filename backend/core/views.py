from decimal import Decimal
from datetime import date,timedelta
import re
from django.contrib.auth import authenticate,login,logout
from django.db import transaction as db_transaction
from django.db.models import Q,Sum
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.decorators import action,api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from .models import *
from .serializers import *
from .engine import FinancialEngine,IN,OUT

def health(request): return JsonResponse({'status':'ok'})
@ensure_csrf_cookie
def csrf(request): return JsonResponse({'ok':True})
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
 email=request.data.get('email','').strip().lower(); password=request.data.get('password',''); name=request.data.get('name','').strip()
 if not email or not password or not name:return Response({'error':'Name, email and password are required.'},status=400)
 if User.objects.filter(email=email).exists():return Response({'error':'Email already registered.'},status=400)
 u=User.objects.create_user(username=email,email=email,password=password,first_name=name)
 Account.objects.create(user=u,name='Main Wallet',kind='cash',opening_balance=Decimal('0'))
 login(request,u); return Response({'user':{'id':u.id,'name':u.first_name,'email':u.email,'currency':u.currency}})
@api_view(['POST'])
@permission_classes([AllowAny])
def signin(request):
 u=authenticate(request,email=request.data.get('email','').strip().lower(),password=request.data.get('password',''))
 if not u:return Response({'error':'Invalid email or password.'},status=400)
 if not u.accounts.exists(): Account.objects.create(user=u,name='Main Wallet',kind='cash',opening_balance=Decimal('0'))
 login(request,u); return Response({'user':{'id':u.id,'name':u.first_name,'email':u.email,'currency':u.currency}})
@api_view(['POST'])
def signout(request): logout(request); return Response({'ok':True})
@api_view(['GET'])
def me(request):
 u=request.user; return Response({'id':u.id,'name':u.first_name or u.username,'email':u.email,'currency':u.currency})
class Owned(viewsets.ModelViewSet):
 permission_classes=[IsAuthenticated]
 def get_queryset(self): return self.queryset.filter(user=self.request.user)
 def perform_create(self,serializer): serializer.save(user=self.request.user)
class AccountViewSet(Owned): queryset=Account.objects.all(); serializer_class=AccountSerializer
class PersonViewSet(Owned): queryset=Person.objects.all(); serializer_class=PersonSerializer
class BudgetViewSet(Owned): queryset=Budget.objects.all(); serializer_class=BudgetSerializer
class GoalViewSet(Owned): queryset=Goal.objects.all(); serializer_class=GoalSerializer
class ReminderViewSet(Owned): queryset=Reminder.objects.all(); serializer_class=ReminderSerializer
class TransactionViewSet(Owned):
 queryset=Transaction.objects.select_related('person','account','destination_account','related_transaction').all(); serializer_class=TransactionSerializer
 def perform_create(self,serializer):
  with db_transaction.atomic():
   data=serializer.validated_data
   if data.get('type')!='transfer' and not data.get('account'):
    account=Account.objects.filter(user=self.request.user).order_by('id').first()
    if not account: account=Account.objects.create(user=self.request.user,name='Main Wallet',kind='cash',opening_balance=Decimal('0'))
    t=serializer.save(user=self.request.user,currency=self.request.user.currency,account=account)
   else: t=serializer.save(user=self.request.user,currency=self.request.user.currency)
   AuditEvent.objects.create(user=self.request.user,entity_type='transaction',entity_id=t.pk,action='created',new_state=FinancialEngine.snapshot(t))
 def perform_update(self,serializer):
  with db_transaction.atomic():
   old=FinancialEngine.snapshot(self.get_object()); t=serializer.save(); AuditEvent.objects.create(user=self.request.user,entity_type='transaction',entity_id=t.pk,action='edited',previous_state=old,new_state=FinancialEngine.snapshot(t))
 @action(detail=True,methods=['post'])
 def reverse(self,request,pk=None):
  t=self.get_object()
  if t.status!='active':return Response({'error':'Transaction is already reversed.'},status=400)
  old=FinancialEngine.snapshot(t)
  with db_transaction.atomic():
   t.status='reversed'; t.save(update_fields=['status','updated_at']); AuditEvent.objects.create(user=request.user,entity_type='transaction',entity_id=t.pk,action='reversed',previous_state=old,new_state={'status':'reversed'})
  return Response({'ok':True})
 def get_queryset(self):
  qs=super().get_queryset(); p=self.request.query_params
  if p.get('status','active')=='active':qs=qs.filter(status='active')
  for field in ['type','category','subcategory','payment_method']:
   if p.get(field):qs=qs.filter(**{field:p.get(field)})
  if p.get('q'):
   q=p['q']; qs=qs.filter(Q(item__icontains=q)|Q(income_source__icontains=q)|Q(reason__icontains=q)|Q(purpose__icontains=q)|Q(description__icontains=q)|Q(notes__icontains=q)|Q(category__icontains=q)|Q(person__name__icontains=q)|Q(location__icontains=q)|Q(shop_store__icontains=q))
  if p.get('from'):qs=qs.filter(date__gte=p['from'])
  if p.get('to'):qs=qs.filter(date__lte=p['to'])
  return qs.order_by('-date','-exact_time','-id')

def _period_stats(user,start,end):
 qs=FinancialEngine.active_qs(user).filter(date__range=(start,end)); z=Decimal('0')
 def total(types): return qs.filter(type__in=list(types)).aggregate(v=Sum('amount'))['v'] or z
 earned=total(IN); spent=total(OUT)
 return {'earned':earned,'spent':spent,'saved':earned-spent,'expense':total({'expense'}),'income':total({'income','salary','money_added'}),'lend':total({'lend'}),'borrow':total({'borrow'}),'help':total({'help'}),'repayment_received':total({'repayment_received'}),'repayment_made':total({'repayment_made'})}
@api_view(['GET'])
def dashboard(request):
 today=date.today(); monday=today-timedelta(days=today.weekday()); month_start=today.replace(day=1); summary=FinancialEngine.summary(request.user)
 monthly=Budget.objects.filter(user=request.user,active=True,period='monthly',start_date__lte=today,end_date__gte=today).order_by('-id').first(); budget=None
 if monthly:
  used=Transaction.objects.filter(user=request.user,status='active',type='expense',date__range=(monthly.start_date,monthly.end_date)).aggregate(v=Sum('amount'))['v'] or Decimal('0')
  budget={'id':monthly.id,'target':monthly.amount,'used':used,'remaining':monthly.amount-used,'percentage':round(float(used/monthly.amount*100),2) if monthly.amount else 0}
 return Response({'summary':summary,'periods':{'today':_period_stats(request.user,today,today),'week':_period_stats(request.user,monday,today),'month':_period_stats(request.user,month_start,today),'total':_period_stats(request.user,date(2000,1,1),today)},'budget':budget})
@api_view(['GET'])
def analytics(request):
 today=date.today(); qs=FinancialEngine.active_qs(request.user); series=[]
 for i in range(13):
  d=today-timedelta(days=12-i); row=qs.filter(date=d); series.append({'label':d.strftime('%a'),'date':d.isoformat(),'earned':sum((x.amount for x in row.filter(type__in=IN)),Decimal('0')),'spent':sum((x.amount for x in row.filter(type__in=OUT)),Decimal('0')),'expense':sum((x.amount for x in row.filter(type='expense')),Decimal('0')),'lend':sum((x.amount for x in row.filter(type='lend')),Decimal('0')),'borrow':sum((x.amount for x in row.filter(type='borrow')),Decimal('0')),'help':sum((x.amount for x in row.filter(type='help')),Decimal('0'))})
 cats={}
 for r in qs.filter(type='expense').values('category').annotate(total=Sum('amount')).order_by('-total')[:10]: cats[r['category'] or 'Other']=r['total']
 return Response({'summary':FinancialEngine.summary(request.user),'series':series,'categories':cats,'type_totals':{t:qs.filter(type=t).aggregate(v=Sum('amount'))['v'] or Decimal('0') for t,_ in Transaction.TYPES}})
@api_view(['GET'])
def reports(request):
 month=request.query_params.get('month') or date.today().strftime('%Y-%m'); y,m=map(int,month.split('-')); qs=FinancialEngine.active_qs(request.user).filter(date__year=y,date__month=m); totals={k:qs.filter(type=k).aggregate(v=Sum('amount'))['v'] or Decimal('0') for k in ['income','salary','expense','lend','borrow','help','repayment_received','repayment_made','money_added','transfer']}; return Response({'month':month,'totals':totals,'summary':FinancialEngine.summary(request.user)})
@api_view(['POST'])
def parse_nl(request):
 text=(request.data.get('text') or '').strip(); amount=re.search(r'(?:৳|tk|taka)?\s*(\d+(?:\.\d+)?)',text,re.I); tm=re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)',text,re.I); proposal={'type':'expense' if any(w in text.lower() for w in ['spent','bought','paid']) else 'income','amount':amount.group(1) if amount else '','exact_time':tm.group(1) if tm else '','item':text.split(' on ')[1].split(' at ')[0] if ' on ' in text else '','description':text}; return Response({'understood_as':proposal,'requires_confirmation':True})