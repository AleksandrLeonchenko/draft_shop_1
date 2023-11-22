from django.db.models.query import QuerySet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import FilterSet, CharFilter
from django_filters import rest_framework as filters
from django.core.exceptions import FieldError
from typing import List, Union, Any, Dict

from .models import ProductInstance


class CustomPaginationProducts(PageNumberPagination):
    """
    Пользовательская пагинация для продуктов.

    Attributes:
    - page_size (int): Определение базового размера страницы.
    - page_query_param (str): Параметр запроса для указания текущей страницы.
    - max_page_size (int): Определение максимального размера страницы.
    """
    page_size: int = 3  # Определение базового размера страницы
    page_query_param: str = 'currentPage'  # Параметр запроса для указания текущей страницы
    max_page_size: int = 20  # Определение максимального размера страницы

    def get_paginated_response(self, data: List[Dict[str, Any]]) -> Response:
        """
        Возвращает ответ с пагинацией для переданных данных.

        Args:
        - data (List[Dict[str, Any]]): Список словарей данных для текущей страницы.

        Returns:
        - Response: Ответ с пагинацией, содержащий текущие элементы страницы, номер текущей страницы
                    и общее количество элементов.
        """
        return Response({
            'items': data,  # Возвращает текущие элементы страницы
            'currentPage': self.page.number,  # Возвращает номер текущей страницы
            'lastPage': self.page.paginator.count,  # Возвращает общее количество элементов
        })


class PrefixedNumberFilter(filters.NumberFilter):
    """
    Класс для конвертации строкового значения во float.

    Attributes:
    - query_param (str): Параметр запроса для извлечения значения и конвертации его во float.
    """

    #  Добавляем новый атрибут query_param к классу PrefixedNumberFilter
    def __init__(self, *args, **kwargs):
        """
        Инициализация нового атрибута query_param к классу PrefixedNumberFilter.

        Args:
        - *args: Позиционные аргументы.
        - **kwargs: Именованные аргументы.
        """
        self.query_param = kwargs.pop('query_param', None)  # Забираем query_param из аргументов
        super().__init__(*args, **kwargs)

    def filter(self, qs: QuerySet, value: float) -> QuerySet:
        """
        Метод фильтрации.

        Args:
        - qs (QuerySet): Набор данных для фильтрации.
        - value (float): Значение фильтра.

        Returns:
        - QuerySet: Отфильтрованный набор данных.
        """
        # Проверяем, есть ли у self.parent атрибут request
        request = getattr(self.parent, 'request', None)  # Извлекаем атрибут 'request' из родительского объекта
        if request and self.query_param:
            value_str = request.GET.get(self.query_param, None)
            if value_str is not None and value_str != '':  # Проверяем, что значение не пустое
                try:
                    value = float(value_str)  # Конвертируем строковое значение во float
                except ValueError:
                    return qs  # Возвращаем исходный QuerySet без изменений

        return super().filter(qs, value)  # Если все в порядке, вызываем родительский метод filter


class PrefixedBooleanFilter(filters.BooleanFilter):
    """
    Класс для конвертации строкового значения в булево.

    Attributes:
    - BOOLEAN_MAP (dict): Словарь для маппинга строковых значений в булевы значения.
    """
    # Определение словаря для маппинга строковых значений в булевы
    BOOLEAN_MAP = {
        'true': True,
        'false': False
    }

    def filter(self, qs: QuerySet, value: bool) -> QuerySet:
        """
        Метод фильтрации.

        Args:
        - qs (QuerySet): Набор данных для фильтрации.
        - value (bool): Значение фильтра.

        Returns:
        - QuerySet: Отфильтрованный набор данных.
        """

        # Получаем у объекта-родителя self.parent атрибут request
        request = getattr(self.parent, 'request', None)
        if request:
            # Получение значения строки из GET-запроса по имени поля фильтрации:
            value_str = request.GET.get(f'filter[{self.field_name}]', None)
            if value_str in self.BOOLEAN_MAP:  # Проверка наличия значения в словаре BOOLEAN_MAP
                value = self.BOOLEAN_MAP[value_str]  # Получаем булево значение из строки, используя словарь BOOLEAN_MAP
            else:
                return qs

        return super().filter(qs, value)  # Родительский метод filter() с примененными значениями фильтрации


class ProductFilter(FilterSet):
    """
    Класс для фильтрации с параметрами фильтрации, например
    /catalog?filter[name]=&filter[minPrice]=100&filter[maxPrice]=1000&filter[freeDelivery]=true

    Attributes:
    - minPrice (PrefixedNumberFilter): Фильтр для минимальной цены товара.
    - maxPrice (PrefixedNumberFilter): Фильтр для максимальной цены товара.
    - freeDelivery (PrefixedBooleanFilter): Фильтр для бесплатной доставки товара.
    - available (PrefixedBooleanFilter): Фильтр для доступности товара.
    - category (PrefixedNumberFilter): Фильтр для категории товара по идентификатору.
    - property (CharFilter): Фильтр для характеристик товара по значению.
    - name (CharFilter): Фильтр для поиска по названию товара без учета регистра символов.

    Permissions:
    - permission_classes (list): Разрешения для доступа к фильтру.
    """
    permission_classes = [AllowAny]
    minPrice = PrefixedNumberFilter(field_name='price', lookup_expr='gte', query_param='filter[minPrice]')
    maxPrice = PrefixedNumberFilter(field_name='price', lookup_expr='lte', query_param='filter[maxPrice]')
    freeDelivery = PrefixedBooleanFilter(field_name='freeDelivery')
    available = PrefixedBooleanFilter(field_name='available')
    category = PrefixedNumberFilter(field_name='category__id')
    property = CharFilter(field_name='specifications__value', lookup_expr='icontains')  # поиск по вх. без учёта рег.
    name = CharFilter(field_name='title', lookup_expr='icontains')  # поиск по вхождению без учёта регистра символов

    class Meta:
        model = ProductInstance
        fields = "__all__"


class CustomOrderingFilter(OrderingFilter):
    """
    Класс для кастомной сортировки.

    Attributes:
    - ordering_field_map (dict): Словарь для маппинга полей сортировки.
    """
    # Словарь для маппинга полей сортировки
    ordering_field_map = {
        'reviews': 'reviews_count'
    }

    def filter_queryset(self, request: Request, queryset: QuerySet,
                        view) -> QuerySet:  # Переопределение метода фильтрации по порядку
        """
        Переопределение метода фильтрации по порядку.

        Args:
        - request (Request): Объект запроса.
        - queryset (QuerySet): Набор данных для сортировки.
        - view (Any): Вид представления.

        Returns:
        - QuerySet: Отфильтрованный набор данных.
        """
        ordering = self.get_ordering(request, queryset, view)  # Получение параметров сортировки из запроса
        if ordering:
            # Применяем наше переопределение
            ordering = [self.ordering_field_map.get(field, field) for field in
                        ordering]  # Применяем маппинг полей сортировки
            try:
                return queryset.order_by(*ordering)  # Пытаемся отсортировать queryset
            except FieldError:
                pass
        return queryset
