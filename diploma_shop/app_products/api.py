from django.db.models.query import QuerySet
from django_filters.rest_framework import FilterSet, OrderingFilter, DjangoFilterBackend, CharFilter
from django.db.models import Avg, Count
from django.utils import timezone
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
    def __init__(self, *args, **kwargs):
        self.query_param = kwargs.pop('query_param', None)
        super().__init__(*args, **kwargs)

    def filter(self, qs: QuerySet, value: float) -> QuerySet:
        request = getattr(self.parent, 'request', None)
        if request and self.query_param:
            value_str = request.GET.get(self.query_param, None)
            if value_str is not None and value_str != '':
                try:
                    value = float(value_str)
                except ValueError:
                    return qs

        return super().filter(qs, value)


class PrefixedBooleanFilter(filters.BooleanFilter):
    BOOLEAN_MAP = {
        'true': True,
        'false': False
    }

    def filter(self, qs: QuerySet, value: bool) -> QuerySet:
        # Проверяем, есть ли у self.parent атрибут request
        request = getattr(self.parent, 'request', None)
        if request:
            value_str = request.GET.get(f'filter[{self.field_name}]', None)
            if value_str in self.BOOLEAN_MAP:
                value = self.BOOLEAN_MAP[value_str]
            else:
                return qs

        return super().filter(qs, value)


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

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
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
        if ordering:
            ordering_field_map = {
                'reviews': 'reviews_count'
            }
            return [ordering_field_map.get(field, field) for field in ordering]
        return ordering

    def get_queryset(self) -> QuerySet:
        queryset = ProductInstance.objects.filter_and_annotate()
        name_filter = self.request.query_params.get('filter[name]', None)

        # Фильтрация
        filterset = ProductFilter(self.request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs
        else:
            # Логирование ошибок фильтрации
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
        products = ProductInstance.objects.filter_and_annotate()[:16]
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
        current_date = timezone.now().date()
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
