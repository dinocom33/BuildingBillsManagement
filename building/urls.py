from django.urls import path
from . import views


app_name = 'building'

urlpatterns = [
    path('create_bill/', views.CreateBillView.as_view(), name='create_bill'),
    # path('create_building/', views.create_building, name='create_building'),
    # path('create_entrance/', views.create_entrance, name='create_entrance'),
    # path('create_apartment/', views.create_apartment, name='create_apartment'),
    path('apartments/', views.apartments, name='apartments'),
    path('expense_dashboard/', views.manage_expenses, name='expense_dashboard'),
    path('create_expense/', views.create_expense, name='create_expense'),
    path('bills/', views.bills, name='bills'),
    path('add_message/', views.add_message, name='create_message'),
    path('messages/', views.messages_view, name='messages'),
    path('message/<int:message_id>/', views.message_view, name='message'),
]
