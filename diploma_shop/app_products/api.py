# import json
import django_filters
# from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Avg, Case, When, Sum, Count, Prefetch, Q
# from django.shortcuts import get_object_or_404
from django.utils import timezone
# from rest_framework import status, generics, filters
# from django.contrib.auth.models import Group
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
# from rest_framework.decorators import parser_classes
# from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView, CreateAPIView, \
    RetrieveUpdateAPIView, RetrieveAPIView
# from rest_framework.mixins import ListModelMixin
# from rest_framework import viewsets
# from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
# from rest_framework.parsers import JSONParser
# from django_filters import rest_framework as filters
from django_filters import FilterSet, CharFilter, NumberFilter, BooleanFilter, ChoiceFilter, filters
# from django.core.cache import cache
# from pdb import set_trace
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import FieldError
from django_filters import rest_framework as filters

# from .forms import BasketDeleteForm
from .models import ProductInstance, Review, Category, Tag
from .serializers import ProductListSerializer, ProductSalesSerializer, ProductDetailSerializer, CategorySerializer, \
    TagSerializer, ReviewCreateSerializer
from .service import CustomPaginationProducts


# from .serializers import *
# from .models import *
# from .service import *

# from django_filters import filters

# class PrefixedNumberFilter(filters.NumberFilter):
#     def filter(self, qs, value):
#         if value is not None:
#             value = self.request.GET.get(f'filter[{self.field_name}]', None)
#         return super().filter(qs, value)

class PrefixedNumberFilter1(filters.NumberFilter):
    def filter(self, qs, value):
        if value in (None, ''):
            return qs
        return super().filter(qs, value)


class PrefixedNumberFilter2(filters.NumberFilter):
    def filter(self, qs, value):
        print(
            f"-----NumberFilter-----Filtering by {self.field_name} with value {value}")  # добавьте этот принт для отладки
        return super().filter(qs, value)


# class PrefixedBooleanFilter(filters.BooleanFilter):
#     def filter(self, qs, value):
#         if value is not None:
#             value = self.request.GET.get(f'filter[{self.field_name}]', None)
#         return super().filter(qs, value)

class PrefixedBooleanFilter1(filters.BooleanFilter):
    def filter(self, qs, value):
        if value in (None, ''):
            return qs
        return super().filter(qs, value)


class PrefixedBooleanFilter2(filters.BooleanFilter):
    def filter(self, qs, value):
        print(f"-----BooleanFilter-----Filtering by {self.field_name} with value {value}")  # принт для отладки
        return super().filter(qs, value)


class PrefixedNumberFilter3(filters.NumberFilter):
    def filter(self, qs, value):
        # Получаем значение из запроса
        # value = self.parent.form.cleaned_data.get(f'filter[{self.field_name}]', None)
        value = self.parent.request.GET.get(f'filter[{self.field_name}]', None)
        print(f"-----NumberFilter-----Filtering by {self.field_name} with value {value}")  # принт для отладки
        if value in (None, ''):
            return qs
        return super().filter(qs, value)


class PrefixedNumberFilter4(filters.NumberFilter):
    """
    Фильтрация по небулевым полям НЕ работает
    """

    def filter(self, qs, value):
        print(f"-----NumberFilter-----Filtering by {self.field_name} with value {value}")

        if value is not None:
            try:
                # Пытаемся преобразовать строку в число
                value = float(value)
            except ValueError:
                # Если преобразование не удалось, возвращаем исходный queryset
                return qs

        return super().filter(qs, value)


# class PrefixedNumberFilter(filters.NumberFilter):
#     def filter(self, qs, value):
#         # Проверяем, есть ли у self.parent атрибут request
#         request = getattr(self.parent, 'request', None)
#         print("-----NumberFilter-----request-----", request)  # принт для отладки
#         if request:
#             value_str = request.GET.get(f'filter[{self.field_name}]', None)
#             print("-----NumberFilter--if request---value_str-----", value_str)  # принт для отладки
#             if value_str is not None and value_str != '':
#                 try:
#                     value = float(value_str)
#                     print("-----NumberFilter--try---value-----", value)  # принт для отладки
#                 except ValueError:
#                     print("-----NumberFilter--except---qs-----", qs)  # принт для отладки
#                     return qs
#
#         return super().filter(qs, value)


class PrefixedNumberFilter(filters.NumberFilter):
    def __init__(self, *args, **kwargs):
        self.query_param = kwargs.pop('query_param', None)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        request = getattr(self.parent, 'request', None)
        if request and self.query_param:
            print("-----Keys in GET-----", request.GET.keys())

            value_str = request.GET.get(self.query_param, None)

            print("-----NumberFilter--if request---value_str-----", value_str)  # принт для отладки
            if value_str is not None and value_str != '':
                try:
                    value = float(value_str)
                    print("-----NumberFilter--try---value-----", value)  # принт для отладки
                except ValueError:
                    print("-----NumberFilter--except---qs-----", qs)  # принт для отладки
                    return qs

        return super().filter(qs, value)


class PrefixedBooleanFilter4(filters.BooleanFilter):
    """
    Фильтрация по булевым полям хорошо работает
    """

    def filter(self, qs, value):
        # Получаем значение из запроса
        # value = self.parent.form.cleaned_data.get(f'filter[{self.field_name}]', None)
        value_str = self.parent.request.GET.get(f'filter[{self.field_name}]', None)
        # print(f"-----BooleanFilter-----Filtering by {self.field_name} with value {value}")  # принт для отладки
        if value_str == 'true':
            value = True
        elif value_str == 'false':
            value = False
        else:
            return qs
        return super().filter(qs, value)


class PrefixedBooleanFilter(filters.BooleanFilter):
    BOOLEAN_MAP = {
        'true': True,
        'false': False
    }

    def filter(self, qs, value):
        # Проверяем, есть ли у self.parent атрибут request
        request = getattr(self.parent, 'request', None)
        if request:
            value_str = request.GET.get(f'filter[{self.field_name}]', None)
            if value_str in self.BOOLEAN_MAP:
                value = self.BOOLEAN_MAP[value_str]
            else:
                return qs

        return super().filter(qs, value)


# class CharFilterInFilter(filters.BaseInFilter, filters.CharFilter):
#     pass


class ProductFilter(FilterSet):
    """
    Класс для фильтрации с параметрами фильтрации, здесь по фронту
    /catalog?filter[name]=&filter[minPrice]=100&filter[maxPrice]=1000&filter[freeDelivery]=true
    """
    permission_classes = [AllowAny]
    minPrice = PrefixedNumberFilter(field_name='price', lookup_expr='gte', query_param='filter[minPrice]')
    maxPrice = PrefixedNumberFilter(field_name='price', lookup_expr='lte', query_param='filter[maxPrice]')
    freeDelivery = PrefixedBooleanFilter(field_name='freeDelivery')
    available = PrefixedBooleanFilter(field_name='available')
    category = PrefixedNumberFilter(field_name='category__id')
    property = CharFilter(field_name='specifications__value', lookup_expr='icontains')
    name = CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = ProductInstance
        fields = "__all__"


class CustomOrderingFilter(OrderingFilter):
    # Карта для переопределения полей сортировки
    ordering_field_map = {
        'reviews': 'reviews_count'
    }

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            # Применяем наше переопределение
            ordering = [self.ordering_field_map.get(field, field) for field in ordering]
            try:
                return queryset.order_by(*ordering)
            except FieldError:
                pass
        return queryset


class ProductListView(ListAPIView):
    """
    Вывод списка продуктов, можно удалить
    """
    permission_classes = (AllowAny,)
    queryset = ProductInstance.objects.filter(available=True)
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews2'))
        return queryset


class CatalogView(ListAPIView):
    """
    /catalog?filter[name]=&filter[minPrice]=0&filter[maxPrice]=24000&filter[freeDelivery]=true
    &filter[available]=true&currentPage=1&sort=price&sortType=dec&limit=20

    /catalog?filter[name]=&filter[minPrice]=0&filter[maxPrice]=54000&filter[freeDelivery]=true
    &filter[available]=true&currentPage=1&sort=reviews_count&sortType=inc&limit=20
    """
    permission_classes = (AllowAny,)
    # queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews2'))
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts
    # filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filter_backends = (DjangoFilterBackend, CustomOrderingFilter,)
    filterset_class = ProductFilter
    # ordering_fields = ['rating', 'price', 'reviews_count', 'date']

    ordering_fields = ['rating', 'price', 'reviews', 'date']
    ordering_field_map = {
        'reviews': 'reviews_count'
    }

    def get_ordering(self):
        ordering = super().get_ordering()
        if ordering:
            ordering_field_map = {
                'reviews': 'reviews_count'
            }
            return [ordering_field_map.get(field, field) for field in ordering]
        return ordering

    def get_queryset(self):
        queryset = ProductInstance.objects.filter_and_annotate()
        name_filter = self.request.query_params.get('filter[name]', None)

        # Фильтрация
        filterset = ProductFilter(self.request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs
        else:
            # Можно добавить логирование ошибок фильтрации
            print(filterset.errors)
        if name_filter:
            queryset = queryset.filter(title__icontains=name_filter)

        # Сортировка
        current_page = self.request.query_params.get('currentPage', None)
        sort = self.request.query_params.get('sort', None)
        sort_type = self.request.query_params.get('sortType', None)
        # Перехват полей для сортировки
        if sort == 'reviews':
            sort = 'reviews_count'
        # Применяем сортировку на основе sort и sortType
        if sort and sort_type:
            direction = '' if sort_type == 'inc' else '-'
            queryset = queryset.order_by(f"{direction}{sort}")
        return queryset


class ProductPopularView(APIView):
    """
    Вывод списка топ-продуктов
    """
    permission_classes = (AllowAny,)

    # def get(self, request):
    #     print('-------+++++------------------', request.user)
    #     products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
    #                :8].annotate(reviews_count=Count('reviews2'))
    #     serializer = ProductListSerializer(products, many=True)
    #     return Response(serializer.data)

    def get(self, request):
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:8]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductLimitedView(APIView):
    """
    Вывод списка продуктов с ограниченным тиражом
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        # products = ProductInstance.objects.filter(available=True, limited_edition=True)[:16].annotate(reviews_count=Count('reviews2'))
        products = ProductInstance.objects.filter_and_annotate()[:16]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSalesView(ListAPIView):
    """
    Вывод списка продуктов по распродаже
    """
    permission_classes = (AllowAny,)
    serializer_class = ProductSalesSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        current_date = timezone.now().date()
        queryset = ProductInstance.objects.filter(dateFrom__lte=current_date, dateTo__gte=current_date, available=True)
        return queryset


class ProductBannersView(APIView):
    """
    Вывод баннера из списка топ-продуктов
    """
    permission_classes = (AllowAny,)

    # def get(self, request):
    #     products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
    #                :8].annotate(reviews_count=Count('reviews2'))
    #     serializer = ProductListSerializer(products, many=True)
    #     return Response(serializer.data)

    def get(self, request):
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:8]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод одного конкретного продукта
    """
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        # product = ProductInstance.objects.get(id=pk, available=True)
        product = ProductInstance.objects.filter_and_annotate(product_ids=[pk]).get(id=pk, available=True)
        average_rating = Review.objects.filter(product=product).aggregate(Avg('rate__value'))

        # Округляем средний рейтинг до одного десятичного знака
        if average_rating['rate__value__avg'] is not None:
            formatted_rating = round(average_rating['rate__value__avg'], 1)
        else:
            formatted_rating = None

        # Сохраняем округленное значение в модель
        product.rating = formatted_rating
        product.save()

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


class CategoryView(APIView):
    """
    Вывод категорий продуктов
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class TagsView(APIView):
    """
    Вывод тегов продуктов
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    """
    Добавление отзыва продукту
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = ReviewCreateSerializer

    def post(self, request, pk):
        author = self.request.user
        review = ReviewCreateSerializer(data=request.data)
        product = ProductInstance.objects.get(id=pk, available=True)

        if review.is_valid():
            if Review.objects.filter(product=product, author=author).exists():
                Review.objects.filter(
                    product=product,
                    author=author
                ).update(
                    rate=review.data['rate'],
                    text=review.data['text']
                )
            else:
                review.save(
                    product=product,
                    author=author,
                )
            return Response(status=201)
        else:
            return Response(status=400)
