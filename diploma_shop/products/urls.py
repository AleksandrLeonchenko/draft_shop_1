from django.urls import path, include

from . import views
from .views import *
from .api import *


# app_name = 'products'


urlpatterns = [
    path('', DraftView.as_view(), name='products_draft'),
    path('products/', ProductListView.as_view(), name='products_list'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='products_detail'),
    # path('review/', ReviewCreateView.as_view(), name='products_review'),
    # path('review/<int:pk>/', ReviewCreateView.as_view(), name='products_review'),
    path('product/<int:pk>/review/', ReviewCreateView.as_view(), name='products_review'),
    # path('rating/', AddRateRatingView.as_view(), name='products_rating'),
    path('product/<int:pk>/rating/', AddRateRatingView.as_view(), name='products_rating'),
    path('tags/', TagsView.as_view(), name='tags'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('products/limited/', ProductLimitedListView.as_view(), name='products_limited'),
    path('products/popular/', ProductPopularListView.as_view(), name='products_popular'),
]