from django.db.models.query import QuerySet
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import ProductInstance, Review, Category, Tag
from .serializers import ProductListSerializer, ProductSalesSerializer, ProductDetailSerializer, CategorySerializer, \
    TagSerializer, ReviewCreateSerializer
from .service import CustomPaginationProducts, ProductFilter, CustomOrderingFilter


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
    Каталог товаров с возможностью фильтрации и сортировки.

    Parameters:
    - permission_classes (list): Разрешения для доступа к представлению.
    - serializer_class: Сериализатор для сериализации данных товаров.
    - pagination_class: Класс пагинации для кастомизации отображения страниц.
    - filter_backends (tuple): Набор фильтров для обработки запросов.
    - filterset_class: Класс фильтров для кастомизации фильтрации товаров.
    - ordering_fields (list): Список полей для сортировки.
    - ordering_field_map (dict): Словарь сопоставления полей для корректной сортировки.

    Methods:
    - get_ordering(): Метод для получения параметров сортировки.
    - get_queryset(): Метод для получения набора данных товаров.

    Query Parameters:
    - filter[name] (str): Фильтр по имени товара.
    - filter[minPrice] (int): Минимальная цена товара.
    - filter[maxPrice] (int): Максимальная цена товара.
    - filter[freeDelivery] (bool): Фильтр для бесплатной доставки товара.
    - filter[available] (bool): Фильтр для доступности товара.
    - sort (str): Параметр сортировки.
    - sortType (str): Тип сортировки.
    - currentPage (int): Номер текущей страницы.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Example:
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

    def get_queryset(self) -> QuerySet:
        """
        Получает набор данных товаров с учетом параметров фильтрации и сортировки.

        Returns:
        - QuerySet: Набор данных товаров.

        Example:
        - Получает набор данных товаров с применением фильтров и сортировки.

        """
        queryset = ProductInstance.objects.filter_and_annotate()
        name_filter = self.request.query_params.get('filter[name]', None)  # Получение фильтра по имени из запроса

        # Фильтрация
        if name_filter:
            queryset = queryset.filter(title__icontains=name_filter)  # Применяем фильтр по имени, если он задан

        # Сортировка
        # current_page = self.request.query_params.get('currentPage', None)  # Текущая страница
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
    Вывод списка топ-продуктов.

    Methods:
    GET - получение списка топ-продуктов.

    Parameters:
    Отсутствуют.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Returns:
    Список топ-продуктов в формате JSON.

    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:8]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductLimitedView(APIView):
    """
    Вывод списка продуктов с ограниченным тиражом.

    Methods:
    GET - получение списка продуктов с ограниченным тиражом.

    Parameters:
    Отсутствуют.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Returns:
    Список продуктов с ограниченным тиражом в формате JSON.

    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        products = ProductInstance.objects.filter_and_annotate()[:16]  # Получение первых 16 отаннотированных продуктов
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSalesView(ListAPIView):
    """
    Вывод списка продуктов по распродаже.

    Methods:
    GET - получение списка продуктов по распродаже.

    Parameters:
    Отсутствуют.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Returns:
    Список продуктов, участвующих в распродаже, в формате JSON.

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
    Вывод баннера из списка топ-продуктов.

    Methods:
    GET - получение баннера.

    Parameters:
    Отсутствуют.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Returns:
    Баннеры, основанные на списке топ-продуктов, в формате JSON.

    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # Использование filter_and_annotate для получения продуктов
        products = ProductInstance.objects.filter_and_annotate().order_by('-sort_index', '-number_of_purchases')[:3]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод информации о конкретном продукте.

    Methods:
    GET - получение информации о продукте по его идентификатору.

    Parameters:
    - pk (int): Идентификатор конкретного продукта.

    Permissions:
    - `AllowAny`: Разрешен доступ для всех пользователей.

    Returns:
    Информация о конкретном продукте, включая средний рейтинг,
    в формате JSON.

    """
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        """
        Получение информации о конкретном продукте.

        Parameters:
        - request (Request): Объект запроса.
        - pk (int): Идентификатор конкретного продукта.

        Returns:
        Информация о продукте в формате JSON.

        """
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
    Класс для вывода списка категорий продуктов.

    Methods:
    - get: Получение списка категорий продуктов.

    Parameters:
    - request (Request): Объект запроса.

    Permissions:
    - AllowAny: Разрешение на доступ без аутентификации.

    Returns:
    Категории продуктов в формате JSON.
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Получение списка категорий продуктов.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        Категории продуктов в формате JSON.

        """
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class TagsView(APIView):
    """
    Класс для вывода тегов продуктов.

    Methods:
    - get: Получение списка тегов продуктов.

    Parameters:
    - request (Request): Объект запроса.

    Permissions:
    - AllowAny: Разрешение на доступ без аутентификации.

    Returns:
    Теги продуктов в формате JSON.
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Получение списка тегов продуктов.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        Теги продуктов в формате JSON.
        """
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    """
    Класс для добавления отзыва продукту.

    Methods:
    - post: Создание отзыва для указанного продукта.

    Parameters:
    - request (Request): Объект запроса.
    - pk (int): ID продукта, для которого добавляется отзыв.

    Permissions:
    - IsAuthenticated: Только аутентифицированным пользователям разрешено добавлять отзывы.

    Returns:
    - 201 Created: Отзыв успешно создан.
    - 400 Bad Request: Некорректный запрос или данные для создания отзыва.
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = ReviewCreateSerializer

    def post(self, request: Request, pk: int) -> Response:
        """
        Создание отзыва для указанного продукта.

        Parameters:
        - request (Request): Объект запроса.
        - pk (int): ID продукта, для которого добавляется отзыв.

        Returns:
        - 201 Created: Отзыв успешно создан.
        - 400 Bad Request: Некорректный запрос или данные для создания отзыва.
        """
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
