import json
import django_filters
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Avg, Case, When, Sum, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, filters
from django.contrib.auth.models import Group
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView, CreateAPIView, \
    RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import JSONParser
from django_filters import rest_framework as filters
from django_filters import FilterSet, CharFilter, NumberFilter, BooleanFilter, ChoiceFilter
from django.core.cache import cache
from pdb import set_trace

from .forms import BasketDeleteForm
from .serializers import *
from .models import *
from .service import *


class ProductFilter(FilterSet):
    """
    Класс для фильтрации с параметрами фильтрации
    """
    permission_classes = (AllowAny,)
    name = CharFilter(field_name='title', lookup_expr='icontains')
    # filter = CharFilter(field_name='title', lookup_expr='icontains')
    minPrice = NumberFilter(field_name='price', lookup_expr='gte')
    maxPrice = NumberFilter(field_name='price', lookup_expr='lte')
    freeDelivery = BooleanFilter(field_name='freeDelivery')
    available = BooleanFilter(field_name='available')
    category = NumberFilter(field_name='category__id')
    property = CharFilter(field_name='specifications__value', lookup_expr='icontains')

    class Meta:
        model = ProductInstance
        fields = []


class ProductListView(ListAPIView):
    """
    Вывод списка продуктов, можно удалить
    """
    permission_classes = (AllowAny,)
    queryset = ProductInstance.objects.filter(available=True)
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
        return queryset


class CatalogView(ListAPIView):
    """
    /catalog/?name=школ - поиск по названию продукта регистронезависимым вхождением "школ" в название продукта
    /catalog/?minPrice=100&maxPrice=1000&freeDelivery=true отфильтрованы продукты с ценой от 100 до 1000 с бесплатной доставкой
    /catalog/?name=школ&minPrice=100&maxPrice=1000&freeDelivery=true
    /catalog/?ordering=-rating (Сортировка по рейтингу в убывающем порядке)
    /catalog/?ordering=price (Сортировка по цене в возрастающем порядке)
    """
    permission_classes = (AllowAny,)
    queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter,)
    filterset_class = ProductFilter
    ordering_fields = ['rating', 'price', 'reviews_count', 'date']
    ordering = ['date']  # default ordering


class ProductPopularView(APIView):
    """
    Вывод списка топ-продуктов
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        print('-------+++++------------------', request.user)
        products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
                   :8].annotate(reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductLimitedView(APIView):
    """
    Вывод списка продуктов с ограниченным тиражом
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        products = ProductInstance.objects.filter(available=True, limited_edition=True)[:16].annotate(
            reviews_count=Count('reviews'))
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

    def get(self, request):
        products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
                   :8].annotate(reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод одного конкретного продукта
    """
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        product = ProductInstance.objects.get(id=pk, available=True)
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


class ProfileView(APIView):
    """
    Отображение, добавление и изменение профиля пользователя,
    email обновляется, но фронтом не отображается
    и аватар нужно обязятельно при обновлении загружать
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = ProfileSerializer

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            print('-------00000------------------', request.user)  # отладочная информация
            print('-------00000------------------', request.session.session_key)  # отладочная информация
        except ObjectDoesNotExist:
            profile = Profile.objects.create(user=request.user)
        serializer = self.serializer_class(profile)
        return Response(serializer.data)

    def post(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = self.serializer_class(profile, data=request.data, partial=True)
        except ObjectDoesNotExist:
            serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]  # Разрешаем неаутентифицированным пользователям делать запрос
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            print('---Login----serializer.is_valid------------------')  # отладочная информация
            print('---Login----session_key------------------', request.session.session_key)  # отладочная информация
            # print('---Login----До очистки сессии---------------')  # отладочная информация
            # request.session.flush()  # Очистка сессии
            # print('---Login----Выполнена очистка сессии------------------')  # отладочная информация
            print('---Login----session_key------------------', request.session.session_key)  # отладочная информация
            print('---Login---- User ID in Session:', request.session.get('_auth_user_id'))
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            user = authenticate(username=username, password=password)
            print('--------Ввели username, password---------', username, '---', password)  # отладочная информация
            if user.is_authenticated:
                # request.session.flush()  # Очистка сессии
                print('---Login----Внутри user.is_authenticated------------------')  # отладочная информация
                # print('---2.5----Очистка сессии---------------')  # отладочная информация
                print('---Login----user------------------', user)  # отладочная информация
                print('---Login----request.user----------', request.user)  # отладочная информация
                print('---Login----session_key-----------', request.session.session_key)  # отладочная информация
                print('---Login---- User ID in Session:', request.session.get('_auth_user_id'))
                login(request, user)
                print('---Login----Вошли------------------')  # отладочная информация
                print('---Login----user------------------', user)  # отладочная информация
                print('---Login----request.user----------', request.user)  # отладочная информация
                print('---Login----session_key-----------', request.session.session_key)  # отладочная информация
                print('---Login---- User ID in Session:', request.session.get('_auth_user_id'))
                # cache.clear()
                return Response({"message": "successful operation"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """
    Регистрация, работает в рест, не работает во фронте, возможно 'name' это не 'fullName'
    """
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    User = get_user_model()
    serializer_class = SignUpSerializer

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            # Исключаем поля slug, avatar и phone из validated_data
            validated_data = {
                key: value for (key, value) in serializer.validated_data.items() if key not in [
                    'slug',
                    'avatar',
                    'phone'
                ]
            }
            # Создаем пользователя без полей slug, avatar и phone
            user = User.objects.create_user(username=validated_data['username'], password=validated_data['password'])
            Profile.objects.create(user=user, fullName=validated_data['fullName'])
            login(request, user)
            return Response({"message": "successful operation"}, status=status.HTTP_200_OK)

        # return Response(serializer.errors)
        return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    Выход из системы
    """
    # permission_classes = (AllowAny,)
    authentication_classes = [SessionAuthentication]

    # authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request):
        print('================================================================')  # отладочная информация
        print('---Logout----Пока не вышли---------')  # отладочная информация
        print('---Logout----request.user----------', request.user)  # отладочная информация
        print('---Logout----session_key-----------', request.session.session_key)  # отладочная информация
        print('---Logout---- User ID in Session:', request.session.get('_auth_user_id'))
        logout(request)
        print('---Logout----Вышли------------------')  # отладочная информация
        # print('---Logout----До очистки сессии---------------')  # отладочная информация
        # request.session.flush()  # Очистка сессии
        # print('---Logout----Выполнена очистка сессии------------------')  # отладочная информация
        print('---Logout----request.user------------------', request.user)  # отладочная информация
        print('---Logout----session_key-----------', request.session.session_key)  # отладочная информация
        print('---Logout---- User ID in Session:', request.session.get('_auth_user_id'))
        # cache.clear()
        return Response({"message": "successful operation"}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Смена пароля
    """
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = (AllowAny,)

    def post(self, request):
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        user = request.user

        # Проверяем, совпадает ли текущий пароль
        if user.check_password(current_password):
            # Обновляем пароль
            user.set_password(new_password)
            user.save()

            return Response({'message': 'successful operation'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Неверный текущий пароль'}, status=status.HTTP_400_BAD_REQUEST)


class UpdateAvatarAPIView(APIView):
    """
    Смена аватара, не пойму для чего, но в свагере есть
    """
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = (AllowAny,)
    serializer_class = ProfileAvatarSerializer

    def post(self, request, *args, **kwargs):
        instance = request.user.shop_profile_user
        serializer = self.serializer_class(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BasketView(APIView):
    """
    Корзина
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = (AllowAny,)
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        # set_trace()  # Здесь выполнение программы будет остановлено
        basket = get_object_or_404(Basket, user=request.user)
        # print('---Basket----BasketView------------')  # отладочная информация
        print('---Basket----request.user----------', request.user)  # отладочная информация
        print('---Basket----session_key-----------', request.session.session_key)  # отладочная информация
        print('---Basket---- User ID in Session:', request.session.get('_auth_user_id'))
        basket_items = basket.items.all()
        product_ids = basket_items.values_list('product_id', flat=True)

        # Используем новый метод менеджера
        products = ProductInstance.objects.filter_and_annotate(product_ids)

        # serializer = BasketProductSerializer(products, many=True)
        serializer = BasketProductSerializer(products, many=True, context={'user': request.user})
        return Response(serializer.data)

    # def post(self, request):
    #     serializer = BasketItemSerializer(data=request.data)
    #     if serializer.is_valid():
    #         basket = Basket.objects.get(user=request.user)
    #         product_id = serializer.validated_data['id']
    #         count = serializer.validated_data['count']
    #         product = ProductInstance.objects.get(id=product_id)
    #         basket_item = BasketItem.objects.create(basket=basket, product=product, count=count)
    #
    #         # serializer = BasketProductSerializer(basket_item.product)
    #
    #         basket_items = basket.items.all()
    #         product_ids = basket_items.values_list('product_id', flat=True)
    #         products = ProductInstance.objects.filter_and_annotate(product_ids)
    #         serializer = BasketProductSerializer(products, many=True)
    #
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket = Basket.objects.get(user=request.user)
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']
            product = ProductInstance.objects.get(id=product_id)

            # Пытаемся получить существующий элемент корзины для данного продукта
            try:
                basket_item = BasketItem.objects.get(basket=basket, product=product)
                # Если существует, обновляем его количество
                basket_item.count += count
                basket_item.save()
            except BasketItem.DoesNotExist:
                # Если не существует, создаем новый элемент корзины
                basket_item = BasketItem.objects.create(basket=basket, product=product, count=count)

            basket_items = basket.items.all()
            product_ids = basket_items.values_list('product_id', flat=True)
            products = ProductInstance.objects.filter_and_annotate(product_ids)
            # serializer = BasketProductSerializer(products, many=True)
            serializer = BasketProductSerializer(products, many=True, context={'user': request.user})

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket = Basket.objects.get(user=request.user)
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']

            try:
                basket_item = BasketItem.objects.get(basket=basket, product_id=product_id)
            except BasketItem.DoesNotExist:
                return Response({"error": "Product not found in basket"}, status=status.HTTP_404_NOT_FOUND)

            if basket_item.count == count:
                basket_item.delete()
            elif basket_item.count > count:
                basket_item.count -= count
                basket_item.save()
            else:
                return Response({"error": "The basket contains fewer items than you're trying to remove"},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Item(s) removed successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIView(APIView):
    # parser_classes = [JSONParser]
    parser_classes = [PlainListJSONParser]
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request, *args, **kwargs):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @transaction.atomic  # использование транзакции для обеспечения целостности данных
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            basket = Basket.objects.get(user=user)  # получаем корзину пользователя
        except Basket.DoesNotExist:
            return Response({'error': 'User does not have a basket'}, status=status.HTTP_400_BAD_REQUEST)

        # Если у пользователя уже есть корзина, просто создаем заказ и привязываем к этой корзине
        order = Order.objects.create(basket=basket)

        # Возвращаем ответ с идентификатором созданного заказа
        print('-------request.data--------', request.data)
        return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)

    # def get(self, request, *args, **kwargs):
    #     orders = Order.objects.all()
    #     serializer = OrderSerializer(orders, many=True)
    #     return Response(serializer.data)


class OrderDetailAPIView1(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer

    def post(self, request, *args, **kwargs):
        try:
            order = self.get_object()  # получение объекта заказа по id
        except Http404:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data  # данные, полученные из тела POST-запроса

        if 'fullName' in data:
            order.basket.user.profile.fullName = data['fullName']
        if 'email' in data:
            order.basket.user.email = data['email']
        if 'phone' in data:
            order.basket.user.profile.phone = data['phone']
        if 'deliveryType' in data:
            order.deliveryType = data['deliveryType']  # предполагается, что у вас есть маппинг для типа доставки
        if 'paymentType' in data:
            order.paymentType = data['paymentType']  # предполагается, что у вас есть маппинг для типа оплаты
        if 'totalCost' in data:
            order.totalCost = data['totalCost']
        if 'status' in data:
            order.status = data['status']  # предполагается, что у вас есть маппинг для статуса
        if 'city' in data:
            order.city = data['city']
        if 'address' in data:
            order.address = data['address']

        # Сохранение изменений
        order.save()
        order.basket.user.profile.save()
        order.basket.user.save()

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_200_OK)


class OrderDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer

    # Маппинг строковых значений на числовые
    delivery_type_mapping = {
        'Доставка': 1,
        'Экспресс-доставка': 2,
    }
    payment_type_mapping = {
        'Онлайн картой': 1,
        'Онлайн со случайного чужого счёта': 2,
    }
    status_mapping = {
        'ожидание платежа': 1,
        'оплачено': 2,
    }

    def post(self, request, *args, **kwargs):
        try:
            order = self.get_object()  # получение объекта заказа по id
        except Http404:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data  # данные, полученные из тела POST-запроса

        if 'fullName' in data:
            order.basket.user.profile.fullName = data['fullName']
        if 'email' in data:
            order.basket.user.email = data['email']
        if 'phone' in data:
            order.basket.user.profile.phone = data['phone']
        if 'deliveryType' in data:
            order.deliveryType = self.delivery_type_mapping.get(data['deliveryType'], order.deliveryType)
        if 'paymentType' in data:
            order.paymentType = self.payment_type_mapping.get(data['paymentType'], order.paymentType)
        if 'totalCost' in data:
            order.totalCost = data['totalCost']
        if 'status' in data:
            order.status = self.status_mapping.get(data['status'], order.status)
        if 'city' in data:
            order.city = data['city']
        if 'address' in data:
            order.address = data['address']

        # Сохранение изменений
        order.save()
        order.basket.user.profile.save()
        order.basket.user.save()

        # return Response(OrderDetailSerializer(order).data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_200_OK)


class PaymentCardAPIView(generics.CreateAPIView):
    """
    Оплата (карта оплаты)
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = PaymentCardSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        number = serializer.validated_data.get('number')
        if int(number) % 2 != 0 or len(str(number)) > 8:
            return Response({'error': 'Invalid card number'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(owner=request.user)

        return Response(status=status.HTTP_200_OK)
        # return Response(serializer.data, status=status.HTTP_200_OK)
