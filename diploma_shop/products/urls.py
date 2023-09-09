from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from . import views
from .views import *
from .api import *


# app_name = 'products'

# router = DefaultRouter()
# router.register(r'basket', BasketViewSet)
# router.register(r'basket', BasketViewSet, basename='basket')

# router = SimpleRouter()
# router.register(r'profile', ProfileViewSet, basename='profile')


urlpatterns = [
    path('', ProductListView.as_view(), name='products_list'),
    # path('sign-in', SignInView.as_view(), name='sign-in'),
    path('sign-in', LoginView.as_view(), name='sign-in'),
    path('sign-up', SignUpView.as_view(), name='sign-up'),
    # path('sign-out', SignOutView.as_view(), name='sign-out'),
    path('sign-out', LogoutView.as_view(), name='sign-out'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('products/popular/', ProductPopularView.as_view(), name='products_popular'),
    path('products/limited/', ProductLimitedView.as_view(), name='products_limited'),
    path('sales/', ProductSalesView.as_view(), name='sales'),
    path('banners/', ProductBannersView.as_view(), name='banners'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('orders/', OrderAPIView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('payment/', PaymentCardAPIView.as_view(), name='payment'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/password', ChangePasswordAPIView.as_view()),
    path('profile/avatar', UpdateAvatarAPIView.as_view()),
    path('tags/', TagsView.as_view(), name='tags'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/review/', ReviewCreateView.as_view(), name='product_review'),
    # path('products/', ProductListView.as_view(), name='products_list'),
    # path('', include(router.urls)),
]
