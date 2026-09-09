from django.urls import include,path
from rest_framework.routers import DefaultRouter
from .views import *
router=DefaultRouter(); router.register('accounts',AccountViewSet); router.register('people',PersonViewSet); router.register('transactions',TransactionViewSet); router.register('budgets',BudgetViewSet); router.register('goals',GoalViewSet); router.register('reminders',ReminderViewSet)
urlpatterns=[path('csrf/',csrf),path('auth/signup/',signup),path('auth/signin/',signin),path('auth/signout/',signout),path('me/',me),path('dashboard/',dashboard),path('analytics/',analytics),path('reports/',reports),path('ai/parse/',parse_nl),path('',include(router.urls))]
