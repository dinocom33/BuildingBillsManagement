from django.urls import path
from . import views

urlpatterns = [
    path('create_bill/', views.create_bill, name='create_bill'),
]
