from django.urls import path, include
from . import views
from .api import BasketView, OrderAPIView, OrderDetailAPIView, PaymentCardAPIView
# from .views import *

# app_name = 'app_orders'

urlpatterns = [
    path('basket', BasketView.as_view(), name='basket'),
    path('orders', OrderAPIView.as_view(), name='order-list'),
    path('order/<int:pk>', OrderDetailAPIView.as_view(), name='order-detail'),
    path('payment', PaymentCardAPIView.as_view(), name='payment'),
]
