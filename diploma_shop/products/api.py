import json
import django_filters
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Avg, Case, When, Sum, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, filters
from django.contrib.auth.models import Group
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
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

from .forms import BasketDeleteForm
from .serializers import *
from .models import *
from .service import *


class ProductFilter(FilterSet):
    """
    Класс для фильтрации с параметрами фильтрации
    """
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

    def get(self, request):
        products = ProductInstance.objects.filter(available=True, limited_edition=True)[:16].annotate(
            reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSalesView(ListAPIView):
    """
    Вывод списка продуктов по распродаже
    """
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

    def get(self, request):
        products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
                   :8].annotate(reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод одного конкретного продукта
    """

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

    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class TagsView(APIView):
    """
    Вывод тегов продуктов
    """

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    """
    Добавление отзыва продукту
    """
    permission_classes = [permissions.IsAuthenticated]

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
    serializer_class = ProfileSerializer

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            print('-------00000------------------', request.user)# отладочная информация
            print('-------00000------------------', request.session.session_key)# отладочная информация
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


# class LoginView(APIView):
#     authentication_classes = [BasicAuthentication]
#     permission_classes = [AllowAny]  # Разрешаем неаутентифицированным пользователям делать запрос
#
#     def post(self, request):
#         user = request.user
#         if user.is_authenticated:
#             login(request, user)
#             return Response({"message": "successful operation"}, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class LoginView(APIView):
#     authentication_classes = [BasicAuthentication]
#     permission_classes = [AllowAny]  # Разрешаем неаутентифицированным пользователям делать запрос
#
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data.get('username')
#             password = serializer.validated_data.get('password')
#             # Аутентификация пользователя
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 if user.is_active:
#                     login(request, user)
#                     print('------------------------------', user)# отладочная информация
#                     print('-------+++++------------------', request.user)# отладочная информация
#                     print('-------+++++------------------', request.session.session_key)# отладочная информация
#                     # В зависимости от вашей системы, вы можете тут вернуть токен или другую информацию
#                     return Response({"message": "successful operation"}, status=status.HTTP_200_OK)
#                 else:
#                     return Response({"error": "This account has been disabled."}, status=status.HTTP_401_UNAUTHORIZED)
#             else:
#                 return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]  # Разрешаем неаутентифицированным пользователям делать запрос

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        print('-------sssss-------------', request.user)# отладочная информация
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            # Аутентификация пользователя
            # user = authenticate(username=username, password=password)
            user = authenticate(username=username, password=password)
            print('--------fffffff---------', username, password)# отладочная информация
            if user.is_authenticated:
                # if user.is_active:
                login(request, user)  # Вход пользователя в систему
                print('------------------------------', user)# отладочная информация
                print('-------+++++------------------', request.user)# отладочная информация
                print('-------+++++------------------', request.session.session_key)# отладочная информация
                return Response({"message": "successful operation"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """
    Регистрация, работает в рест, не работает во фронте, возможно 'name' это не 'fullName'
    """
    User = get_user_model()

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
    # authentication_classes = [SessionAuthentication]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request):
        print('-------xxxxx------------------', request.user)# отладочная информация
        logout(request)
        print('-------xxxxx333------------------', request.user)# отладочная информация
        return Response({"message": "successful operation"}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Смена пароля
    """
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]
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

    def get(self, request):
        basket = get_object_or_404(Basket, user=request.user)
        basket_items = basket.items.all()
        product_ids = basket_items.values_list('product_id', flat=True)

        # Используем новый метод менеджера
        products = ProductInstance.objects.filter_and_annotate(product_ids)

        serializer = BasketProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket = Basket.objects.get(user=request.user)
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']
            product = ProductInstance.objects.get(id=product_id)
            basket_item = BasketItem.objects.create(basket=basket, product=product, count=count)
            serializer = BasketProductSerializer(basket_item.product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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


class OrderAPIView(ListCreateAPIView):
    """
    Заказы
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"orderId": serializer.instance.id}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer


class PaymentCardAPIView(generics.CreateAPIView):
    """
    Оплата (карта оплаты)
    """
    permission_classes = [permissions.IsAuthenticated]
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
