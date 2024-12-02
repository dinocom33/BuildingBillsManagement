from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ResetPasswordView

urlpatterns = [
    path('create_resident/', views.RegisterView.as_view(), name='create_resident'),
    path('activate/<uidb64>/<token>', views.ActivateAccountView.as_view(), name='activate'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('my_bills/', views.MyBillsView.as_view(), name='my_bills'),
    path('pay_bill/<int:bill_id>/', views.PayBillView.as_view(), name='pay_bill'),
    path('', views.ResidentsView.as_view(), name='residents'),
]
