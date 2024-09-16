from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ResetPasswordView

urlpatterns = [
    path('create_resident/', views.register, name='create_resident'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my_bills/', views.my_bills, name='my_bills'),
    path('pay_bill/<int:bill_id>/', views.pay_bill, name='pay_bill'),
    path('residents/', views.residents, name='residents'),
]
