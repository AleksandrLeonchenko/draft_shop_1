import json

import django_filters
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Avg, Case, When, Sum, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, filters
from django.contrib.auth.models import Group
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .forms import BasketDeleteForm
from .serializers import *
from .models import *
from .service import *


class ProductListView(ListAPIView):
    """
    Вывод списка продуктов
    """
    queryset = ProductInstance.objects.filter(available=True)
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
        return queryset


class CatalogView(ListAPIView):
    """
    Вывод каталога с сортировкой, окно с сортировкой не выводится в рест, с "?" в строке работает,
    но на фронте не работает.
    Сортировка по количеству покупок по возрастанию: ?sort_by=number_of_purchases&sort_direction=asc.
    Сортировка по цене по убыванию: ?sort_by=price&sort_direction=desc.
    Сортировка по количеству отзывов по возрастанию: ?sort_by=reviews&sort_direction=asc.
    Сортировка по новизне по убыванию: ?sort_by=date&sort_direction=desc.
    Сортировка по количеству покупок по возрастанию и фильтрацией по цене: ?ordering=number_of_purchases&price=500
    Сортировка с фильтрацией по названию и тегам: ?title=video&tags=1,2,3

    Поиск по по вхождению слова "школьник", по цене от 0 до 1000, freeDelyvery=True и available=True:
    http://127.0.0.1:8000/api/catalog/?filter=школьник&minPrice=0&maxPrice=1000&freeDelyvery=True&available=True

    Сортировка на фронте работает, но некорректно - либо по возрастанию либо по убыванию
    """

    queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts
    filter_backends = [OrderingFilter, DjangoFilterBackend, filters.SearchFilter]  # Добавлен фильтр поиска
    # filterset_class = ProductFilter

    ordering_fields = ['rating', 'price', 'reviews_count', 'date']  # Поля для сортировки
    filterset_fields = ['title', 'price', 'available', 'freeDelivery', 'tags']  # Поля для фильтрации
    search_fields = ['title', 'description']  # Поля для поиска

    def get_queryset(self):
        queryset = super().get_queryset()

        # Получаем параметры поиска из GET-запроса
        search_text = self.request.GET.get('filter')
        min_price = self.request.GET.get('minPrice')
        max_price = self.request.GET.get('maxPrice')
        free_delivery = self.request.GET.get('freeDelyvery')
        available = self.request.GET.get('available')
        ordering = self.request.GET.get('sort')

        # Параметры поиска
        if search_text:
            # queryset = queryset.filter(
            #     Q(title__icontains=search_text) | Q(description__icontains=search_text)
            # )
            queryset = queryset.filter(Q(title__icontains=search_text))
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if free_delivery:
            queryset = queryset.filter(freeDelivery=free_delivery)
        if available:
            queryset = queryset.filter(available=available)

        # Сортировка результатов
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)

        return queryset


class ProductPopularView(APIView):
    """
    Вывод списка топ-продуктов
    """

    def get(self, request):
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
        # email = Review.objects.filter(product=product)
        product.rating = average_rating['rate__value__avg']
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
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
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


# class SignInView(APIView):
#     """
#     Вход
#     """
#     authentication_classes = [SessionAuthentication]
#     serializer_class = LoginSerializer
#
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data.get('username')
#             password = serializer.validated_data.get('password')
#
#             user = authenticate(request, username=username, password=password)
#
#             if user is not None:
#                 login(request, user)
#                 return Response({'message': 'Вы успешно вошли в систему!'})
#
#         return Response({'error': 'Неверные учетные данные'})


class LoginView(APIView):
    """
    Вход в систему
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({'message': 'Вы успешно вошли в систему!'})

        return Response({'error': 'Неверные учетные данные'}, status=400)


class SignUpView(APIView):
    """
    Регистрация, работает в рест, не работает во фронте, возможно 'name' это не 'fullName'
    """

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
            return Response({'message': 'Пользователь успешно зарегистрирован'})

        return Response(serializer.errors)


# class SignOutView(APIView):
#     """
#     Выход
#     """
#
#     def post(self, request: Request) -> Response:
#         logout(request)
#         return Response(status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Выход из системы
    """
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        logout(request)
        return Response({'message': 'Вы успешно вышли из системы!'})


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

            return Response({
                'message': 'Пароль успешно изменен'
            })
        else:
            return Response({
                'message': 'Неверный текущий пароль'
            }, status=status.HTTP_400_BAD_REQUEST)


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
        products = ProductInstance.objects.filter(id__in=product_ids, available=True).annotate(
            reviews_count=Count('reviews'))
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
        basket = Basket.objects.get(user=request.user)
        serializer = DeleteBasketItemSerializer(data=request.data)
        if serializer.is_valid():
            item_id = serializer.validated_data['id']
            item_count = serializer.validated_data['count']
            basket_item = BasketItem.objects.get(id=item_id, basket=basket)
            basket_item.count -= item_count
            if basket_item.count <= 0:
                basket_item.delete()
            else:
                basket_item.save()
            products = ProductInstance.objects.filter(id=basket_item.product_id, available=True).annotate(
                reviews_count=Count('reviews'))
            serializer = BasketProductSerializer(products, many=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class BasketViewSet(viewsets.ModelViewSet):
#     queryset = Basket.objects.all()
#     serializer_class = BasketSerializer
#
#     # form_class = BasketDeleteForm
#
#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         self.perform_destroy(instance)
#         return Response(serializer.data)


class OrderAPIView(ListCreateAPIView):
    """
    Заказы
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderDetailAPIView(generics.RetrieveAPIView):
    """
    Экземпляр заказа
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # def post(self, request, *args, **kwargs):
    #     order = self.get_object()
    #     serializer = self.serializer_class(order, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_200_OK)
