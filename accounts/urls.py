from django.urls import path
from . import views

urlpatterns = [
    path('create_resident/', views.register, name='create_resident'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('pay_bill/<int:bill_id>/', views.pay_bill, name='pay_bill'),
]
