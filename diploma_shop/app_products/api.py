from django.db.models.query import QuerySet
from django_filters.rest_framework import FilterSet, OrderingFilter, DjangoFilterBackend, CharFilter
from django.db.models import Avg, Count
from django.utils import timezone
from django.http import QueryDict
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import FieldError
from django_filters import rest_framework as filters

from .models import ProductInstance, Review, Category, Tag
from .serializers import ProductListSerializer, ProductSalesSerializer, ProductDetailSerializer, CategorySerializer, \
    TagSerializer, ReviewCreateSerializer
from .service import CustomPaginationProducts


class PrefixedNumberFilter(filters.NumberFilter):
    """
    Класс для конвертации строкового значения во float
    """

    #  Добавляем новый атрибут query_param к классу PrefixedNumberFilter
    def __init__(self, *args, **kwargs):
        self.query_param = kwargs.pop('query_param', None)  # Забираем query_param из аргументов
        super().__init__(*args, **kwargs)

    def filter(self, qs: QuerySet, value: float) -> QuerySet:
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
    Класс для конвертации строкового значения в булево
    """
    # Определение словаря для маппинга строковых значений в булевы
    BOOLEAN_MAP = {
        'true': True,
        'false': False
    }

    def filter(self, qs: QuerySet, value: bool) -> QuerySet:
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
    Класс для кастомной сортировки
    """
    # Словарь для маппинга полей сортировки
    ordering_field_map = {
        'reviews': 'reviews_count'
    }

    def filter_queryset(self, request: Request, queryset: QuerySet,
                        view) -> QuerySet:  # Переопределение метода фильтрации по порядку
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


class ProductListView(ListAPIView):
    """
    Вывод списка продуктов, можно удалить
    """
    permission_classes = [AllowAny]
    queryset = ProductInstance.objects.filter(available=True)
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self) -> QuerySet:
        queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews2'))
        return queryset


class CatalogView(ListAPIView):
    """
    Каталог с фильтрацией и сортировкой, пример:

    /catalog?filter[name]=&filter[minPrice]=0&filter[maxPrice]=24000&filter[freeDelivery]=true
    &filter[available]=true&currentPage=1&sort=price&sortType=dec&limit=20

    /catalog?filter[name]=&filter[minPrice]=0&filter[maxPrice]=54000&filter[freeDelivery]=true
    &filter[available]=true&currentPage=1&sort=reviews_count&sortType=inc&limit=20
    """
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts
    filter_backends = (DjangoFilterBackend, CustomOrderingFilter,)
    filterset_class = ProductFilter
    ordering_fields = ['rating', 'price', 'reviews', 'date']
    ordering_field_map = {
        'reviews': 'reviews_count'
    }

    def get_ordering(self) -> list[str]:
        ordering = super().get_ordering()
        if ordering:  # Если параметры сортировки есть
            ordering_field_map = {  # Словарь для переопределения полей сортировки
                'reviews': 'reviews_count'
            }
            return [ordering_field_map.get(field, field) for field in ordering]  # Применяем маппинг полей сортировки
        return ordering  # Или возвращаем исходные параметры сортировки

    def get_queryset(self) -> QuerySet:
        queryset = ProductInstance.objects.filter_and_annotate()
        # name_filter = self.request.query_params.get('filter[name]', None)  # Получение фильтра по имени из запроса
        name_filter = None
        filter_param = self.request.query_params.get('filter', None)  # Получение фильтра по имени из запроса
        if filter_param and '=' in filter_param:
            name_filter = filter_param.split('=')[-1]

        # Фильтрация
        filterset = ProductFilter(self.request.GET, queryset=queryset)  # Применение фильтров к набору данных
        if filterset.is_valid():
            queryset = filterset.qs  # Применяем фильтры к набору данных
        else:
            # Логирование ошибок фильтрации
            print(filterset.errors)
        if name_filter:
            queryset = queryset.filter(title__icontains=name_filter)  # Применяем фильтр по имени, если он задан

        # Сортировка
        current_page = self.request.query_params.get('currentPage', None)  # Текущая страница
        sort = self.request.query_params.get('sort', None)  # Параметр сортировки
        sort_type = self.request.query_params.get('sortType', None)  # Тип сортировки
        # Перехват полей для сортировки
        if sort == 'reviews':
            sort = 'reviews_count'  # Если сортировка по отзывам, изменяем параметр сортировки
        # Применяем сортировку на основе sort и sortType
        if sort and sort_type:  # Если заданы параметр и тип сортировки
            direction = '' if sort_type == 'inc' else '-'  # Определяем направление сортировки
            queryset = queryset.order_by(f"{direction}{sort}")  # Применяем сортировку к набору данных
        return queryset


class ProductPopularView(APIView):
    """
    Вывод списка топ-продуктов
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:8]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductLimitedView(APIView):
    """
    Вывод списка продуктов с ограниченным тиражом
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        products = ProductInstance.objects.filter_and_annotate()[:16]  # Получение первых 16 отаннотированных продуктов
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSalesView(ListAPIView):
    """
    Вывод списка продуктов по распродаже
    """
    permission_classes = [AllowAny]
    serializer_class = ProductSalesSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self) -> QuerySet:
        current_date = timezone.now().date()  # Получение текущей даты
        queryset = ProductInstance.objects.filter(dateFrom__lte=current_date, dateTo__gte=current_date, available=True)
        return queryset


class ProductBannersView(APIView):
    """
    Вывод баннера из списка топ-продуктов
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:3]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод одного конкретного продукта
    """
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        product = ProductInstance.objects.filter_and_annotate(product_ids=[pk]).get(id=pk, available=True)
        # Получение среднего рейтинга продукта на основе отзывов:
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
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class TagsView(APIView):
    """
    Вывод тегов продуктов
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
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

    def post(self, request: Request, pk: int) -> Response:
        author = self.request.user
        review = ReviewCreateSerializer(data=request.data)
        product = ProductInstance.objects.get(id=pk, available=True)

        if review.is_valid():
            # Проверяем, существует ли уже отзыв от этого пользователя на данный продукт
            if Review.objects.filter(product=product, author=author).exists():
                Review.objects.filter(  # Если существует, то обновляем отзыв и рейтинг
                    product=product,
                    author=author
                ).update(
                    rate=review.data['rate'],
                    text=review.data['text']
                )
            else:
                review.save(  # Если нет, то сохраняем новый отзыв
                    product=product,
                    author=author,
                )
            return Response(status=201)
        else:
            return Response(status=400)
