from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from . import views
from .views import *
from .api import *


# app_name = 'products'

# router = DefaultRouter()
# router.register(r'catalog', CatalogViewSet, basename='catalog')

# router = SimpleRouter()
# router.register(r'profile', ProfileViewSet, basename='profile')


urlpatterns = [
    path('', ProductListView.as_view(), name='products_draft'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    # path('catalog/<int:id>/', ProductDetailView.as_view(), name='catalog_detail'),
    path('products/', ProductListView.as_view(), name='products_list'),
    # path('products/popular/', ProductPopularListView.as_view(), name='products_popular'),
    path('products/popular/', ProductPopularView.as_view(), name='products_popular'),
    path('products/limited/', ProductLimitedView.as_view(), name='products_limited'),
    path('sales/', ProductSalesView.as_view(), name='sales'),

    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/review/', ReviewCreateView.as_view(), name='product_review'),

    path('tags/', TagsView.as_view(), name='tags'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('banners/', ProductBannersView.as_view(), name='banners'),

    path('profile/', ProfileView.as_view(), name='profile'),
    # path('profile/', ProfileView.as_view()),
    path('profile/password', ChangePasswordAPIView.as_view()),
    path('profile/avatar', UpdateAvatarAPIView.as_view()),
    path('sign-in', SignInView.as_view(), name='sign-in'),
    path('sign-up', SignUpView.as_view(), name='sign-up'),
    path('sign-out', SignOutView.as_view(), name='sign-out'),

    # path('profile/', include(routers.urls), name='profile'),
    # path('', include(router.urls)),
    # path('sign-in', SignInView.as_view(), name='sign-in'),
    # path('sign-in', ExampleView.as_view(), name='sign-in'),
    # path('sign-in/', include('rest_framework.urls')),

    # path('', include(router.urls), name='view_set'),
]
