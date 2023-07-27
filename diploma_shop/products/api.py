from django.db import models
from django.db.models import Avg, Case, When, Sum, Count
from rest_framework import generics
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import *
from .models import *
from .service import *


class ProductListView(APIView):
    """Вывод списка продуктов, версия 2"""

    def get(self, request):
        products = ProductInstance.objects.filter(available=True)
        serializer = ProductListSerializer(products, many=True)

        return Response(serializer.data)


# class ProductLimitedListView(ListAPIView):
#     """Вывод списка продуктов с ограниченным тиражом, версия 1"""
#     queryset = ProductInstance.objects.filter(available=True, ogr_tirag=True)
#     serializer_class = ProductLimitedSerializer


class ProductLimitedListView(APIView):
    """Вывод списка продуктов с ограниченным тиражом, версия 2"""

    def get(self, request):
        product = ProductInstance.objects.filter(
            available=True,
            ogr_tirag=True
        ).annotate(
            reviews_count=Count('reviews')
        )
        serializer = ProductLimitedSerializer(product, many=True)

        return Response(serializer.data)


class ProductPopularListView(APIView):
    """Вывод списка топ-продуктов"""

    def get(self, request):
        product = ProductInstance.objects.filter(
            available=True,
            ogr_tirag=True
        ).annotate(
            reviews_count=Count('reviews')
        )
        serializer = ProductLimitedSerializer(product, many=True)

        return Response(serializer.data)


class ProductDetailView(APIView):
    def get(self, request, pk):
        product = ProductInstance.objects.get(id=pk, available=True)
        average_rating = Rating.objects.filter(product=product).aggregate(Avg('rating_value__value'))
        for i in average_rating:
            print('-------*******', i, '*******-------')
        product.rating = average_rating['rating_value__value__avg']
        print('-------*******', product.rating, '*******-------')
        product.save()
        serializer = ProductDetailSerializer(product)

        return Response(serializer.data)


class CategoryView(APIView):
    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class TagsView(ListAPIView):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer


# class ReviewCreateView(APIView):
#     """Добавление отзыва продукту нулевая версия"""
#     def post(self, request):
#         review = ReviewCreateSerializer(data=request.data)
#         if review.is_valid():
#             review.save()
#         return Response(status=201)


# class ReviewCreateView(APIView):
#     """Добавление отзыва продукту первая версия, где рейтинг ставится отдельно"""
#
#     def post(self, request):
#         author = self.request.user
#         review = ReviewCreateSerializer(data=request.data)
#         rating = Rating.objects.get(author=author, product=request.data['product'])
#         rate = rating.rating_value.value
#
#         if review.is_valid():
#             review.save(
#                 author=author,
#                 rate=rate
#             )
#             # review.save(ip=get_client_ip(request), author=author)
#             return Response(status=201)
#         else:
#             return Response(status=400)


# class ReviewCreateView(generics.CreateAPIView):
#     """Добавление отзыва продукту вторая версия, где рейтинг ставится здесь же"""
#     serializer_class = ReviewCreateSerializer


class ReviewCreateView(APIView):
    """Добавление отзыва продукту третья версия, где рейтинг ставится здесь же и в URL присутствует pk"""

    def post(self, request, pk):
        author = self.request.user
        review = ReviewCreateSerializer(data=request.data)

        if review.is_valid():
            review.save(
                product=ProductInstance.objects.get(id=pk, available=True),
                author=author,
            )
            return Response(status=201)
        else:
            return Response(status=400)


# class AddRateRatingView(APIView):
#     """Добавление рейтинга продукту первая версия"""
#
#     def post(self, request):
#         serializer = RatingCreateSerializer(data=request.data)
#         author = self.request.user
#         if serializer.is_valid():
#             serializer.save(
#                 # ip=get_client_ip(request),
#                 author=author
#             )
#             return Response(status=201)
#         else:
#             return Response(status=400)


class AddRateRatingView(APIView):
    """Добавление рейтинга продукту вторая версия, где в URL присутствует pk"""

    def post(self, request, pk):
        author = self.request.user
        serializer = RatingCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                product=ProductInstance.objects.get(id=pk, available=True),
                author=author
            )
            return Response(status=201)
        else:
            return Response(status=400)
