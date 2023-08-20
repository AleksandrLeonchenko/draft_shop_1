import json

import django_filters
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Avg, Case, When, Sum, Count, Prefetch
from rest_framework import status, generics, filters
from django.contrib.auth.models import Group
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import *
from .models import *
from .service import *


# class ProductListView(ListAPIView):
#     """Вывод списка продуктов, версия 1"""
#     queryset = ProductInstance.objects.filter(available=True)
#     serializer_class = ProductListSerializer
#     pagination_class = CustomPaginationProducts

class ProductListView(ListAPIView):
    """
    Вывод списка продуктов, работает
    """
    queryset = ProductInstance.objects.filter(available=True)
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
        return queryset


# class CatalogViewSet(ModelViewSet):
#     # queryset = ProductInstance.objects.filter(available=True)
#     queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
#     serializer_class = ProductListSerializer
#     filter_backends = [DjangoFilterBackend, OrderingFilter]
#     # filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
#     filterset_fields = ['category']
#     ordering_fields = ['number_of_purchases', 'price', 'reviews', 'date']


class CatalogView(ListAPIView):
    """
    Вывод каталога с сортировкой, окно с сортировкой не выводится в рест, но с "?" в строке работает,
    но на фронте не работает.
    Сортировка по количеству покупок по возрастанию: ?sort_by=number_of_purchases&sort_direction=asc.
    Сортировка по цене по убыванию: ?sort_by=price&sort_direction=desc.
    Сортировка по количеству отзывов по возрастанию: ?sort_by=reviews&sort_direction=asc.
    Сортировка по новизне по убыванию: ?sort_by=date&sort_direction=desc.
    Сортировка по количеству покупок по возрастанию и фильтрацией по цене: ?ordering=number_of_purchases&price=500
    Сортировка с фильтрацией по названию и тегам: ?title=video&tags=1,2,3
    """
    # queryset = ProductInstance.objects.filter(available=True)
    queryset = ProductInstance.objects.filter(available=True).annotate(reviews_count=Count('reviews'))
    serializer_class = ProductListSerializer
    pagination_class = CustomPaginationProducts
    filter_backends = [OrderingFilter, DjangoFilterBackend]

    ordering_fields = ['number_of_purchases', 'price', 'reviews_count', 'date']
    filterset_fields = ['title', 'price', 'count', 'freeDelivery', 'tags']

    # pagination_class = CustomPaginationProducts
    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     # Применение фильтра формы фильтрации
    #     category = self.request.query_params.get('category')
    #     if category:
    #         queryset = queryset.filter(category=category)
    #     return queryset


# class ProductPopularListView(ListAPIView):
#     serializer_class = ProductPopularSerializer
#
#     def get_queryset(self):
#         # queryset = ProductInstance.objects.order_by('-sort_index', '-number_of_purchases')[:8]
#         queryset = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
#                    :8].annotate(reviews_count=Count('reviews'))
#         return queryset


class ProductPopularView(APIView):
    """
    Вывод списка топ-продуктов, работает
    """

    def get(self, request):
        products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
                   :8].annotate(reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductLimitedView(APIView):
    """
    Вывод списка продуктов с ограниченным тиражом, работает
    """

    def get(self, request):
        products = ProductInstance.objects.filter(available=True, limited_edition=True)[:16].annotate(
            reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductSalesView(ListAPIView):
    """
    Вывод списка продуктов по распродаже, работает
    """
    serializer_class = ProductSalesSerializer
    pagination_class = CustomPaginationProducts

    def get_queryset(self):
        current_date = timezone.now().date()
        queryset = ProductInstance.objects.filter(dateFrom__lte=current_date, dateTo__gte=current_date, available=True)
        return queryset


class ProductBannersView(APIView):
    """
    Вывод баннера из списка топ-продуктов, работает
    """

    def get(self, request):
        products = ProductInstance.objects.filter(available=True).order_by('-sort_index', '-number_of_purchases')[
                   :8].annotate(reviews_count=Count('reviews'))
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    """
    Вывод одного конкретного продукта, работает
    """

    def get(self, request, pk):
        product = ProductInstance.objects.get(id=pk, available=True)
        average_rating = Review.objects.filter(product=product).aggregate(Avg('rate__value'))
        # email = Review.objects.filter(product=product).
        # print('---------***------x---', x, '---***---')
        product.rating = average_rating['rate__value__avg']
        product.save()
        serializer = ProductDetailSerializer(product)

        return Response(serializer.data)


class CategoryView(APIView):
    """
    Вывод категорий продуктов, работает
    """

    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


# class TagsView(ListAPIView):
#     queryset = Tag.objects.all()
#     serializer_class = TagSerializer


class TagsView(APIView):
    """
    Вывод тегов продуктов, работает
    """

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    """
    Добавление отзыва продукту, работает
    """

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


# class ProfileView(APIView):
#     """Отображение, добавление и изменение профиля пользователя"""
#
#     # parser_classes = (FileUploadParser,)
#     # parser_classes = (MultiPartParser,)
#
#     # headers: {
#     #     'Content-Type': 'multipart/form-data'
#     # }
#
#     def get(self, request):
#         user = request.user
#         profile = Profile.objects.get(user=user)
#         serializer = ProfileSerializer(profile)
#         return Response(serializer.data)
#
#     # def post(self, request: Request) -> Response:
#     #     user = request.user
#     #     # email = user.email
#     #     profile = Profile.objects.get(user=user)
#     #     serializer = ProfileSerializer(profile, data=request.data, email='user.email', partial=True)
#     #     if serializer.is_valid():
#     #         serializer.save()
#     #         return Response(serializer.data)
#     #     # user_data = json.loads(request.body)
#     #     # full_name = user_data.get('fullName')
#     #     # email = user_data.get('email')
#     #     # phone = user_data.get('phone')
#     #     # Profile.objects.update(user=user, fullName=full_name, email=email, phone=phone)
#     #     # return Response(status=status.HTTP_200_OK)
#     #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def post1(self, request):
#         user = request.user
#         profile = Profile.objects.get(user=user)
#         avatar = AvatarsImages.objects.get(profile=profile)
#         # serializer = ProfileSerializer(data=request.data, files=request.FILES)
#         serializer = ProfileSerializer(data=request.data)
#         # serializer.is_valid(raise_exception=True)
#         # serializer.save()
#         if serializer.is_valid():
#             serializer.save()
#             avatar.src = serializer.avatar
#             # profile.fullName = serializer.fullName
#             user.email = serializer.email
#             # profile.phone = serializer.phone
#             profile.save()
#             avatar.save()
#
#             return Response(serializer.data)
#
#         x = profile.user
#         print('***---x---***', x, '-------*******')
#         yyy = profile.fullName
#         print('***---fullName---***', yyy, '-------*******')
#         zzz = avatar.src
#         print('***---avatar.src---***', zzz, '-------*******')
#         zzzyyy = user.email
#         print('***---email---***', zzzyyy, '-------*******')
#         zzzyyyxxx = profile.phone
#         print('***---profile.phone---***', zzzyyyxxx, '-------*******')
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def post(self, request):
#         user = request.user
#         profile = Profile.objects.get(user=user)
#         print('***---profile.user---***', profile.user, '-------*******')
#         print('***---profile.fullName---***', profile.fullName, '-------*******')
#         print('***---profile.phone---***', profile.phone, '-------*******')
#         print('***---user.email---***', profile.user.email, '-------*******')
#         # avatar = AvatarsImages.objects.get(profile=profile)
#         # print('***---avatar.src---***', avatar.src, '-------*******')
#         serializer = ProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             print('***---зашёл в иф---***')
#
#             serializer.save()
#             print('***---2serializer.data---***', serializer.data, '-------*******')
#         return Response(serializer.data)


# class ProfileView(APIView):
#     """
#     версия 1
#     """
#     # def get(self, request):
#     #     profile = Profile.objects.get(user=request.user)
#     #     serializer = ProfileSerializer(profile)
#     #     return Response(serializer.data)
#     def get(self, request):
#         try:
#             profile = Profile.objects.get(user=request.user)
#         except ObjectDoesNotExist:
#             profile = Profile.objects.create(user=request.user)
#         serializer = ProfileSerializer(profile)
#         return Response(serializer.data)
#
#     def post(self, request):
#         serializer = ProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def put(self, request):
#         profile = Profile.objects.get(user=request.user)
#         serializer = ProfileSerializer(profile, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class ProfileView(APIView):
#     """
#     версия 2
#     """
#     serializer_class = ProfileSerializer
#
#     def get(self, request):
#         profiles = Profile.objects.all()
#         serializer = self.serializer_class(profiles, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ProfileView(APIView):
#     """
#     версия 3
#     """
#     serializer_class = ProfileSerializer
#
#     def get(self, request):
#         try:
#             profile = Profile.objects.get(user=request.user)
#         except ObjectDoesNotExist:
#             profile = Profile.objects.create(user=request.user)
#         serializer = ProfileSerializer(profile)
#         return Response(serializer.data)
#
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    """
    Отображение, добавление и изменение профиля пользователя,
    email обновляется, но фронтом не отображается
    и аватар нужно обязятельно при обновлении загружать
    """
    serializer_class = ProfileSerializer

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


# class ProfileView(RetrieveUpdateAPIView):
#     serializer_class = ProfileSerializer
#     queryset = Profile.objects.all()

class SignInView(APIView):
    """
    Вход
    """
    authentication_classes = [SessionAuthentication]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return Response({'message': 'Вы успешно вошли в систему!'})

        return Response({'error': 'Неверные учетные данные'})


# class SignInView(APIView):
#     """
#     работает 1
#     """
#     permission_classes = (permissions.AllowAny,)
#
#     def post(self, request, format=None):
#         serializer = SignInSerializer(data=self.request.data,
#                                      context={'request': self.request})
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         login(request, user)
#         return Response(None, status=status.HTTP_202_ACCEPTED)


# class SignInView(APIView):
#     authentication_classes = [SessionAuthentication, BasicAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, format=None):
#         content = {
#             'user': str(request.user),  # `django.contrib.auth.User` instance.
#             'auth': str(request.auth),  # None
#         }
#         return Response(content)

# class SignInView(APIView):
#     def post(self, request) -> Response:
#         serializer_data = list(request.POST.keys())[0]
#         user_data = json.loads(serializer_data)
#         username = user_data.get('username')
#         password = user_data.get('password')
#         try:
#             user = User.objects.create_user(username=username, password=password)
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return Response(status=status.HTTP_201_CREATED)
#         except Exception:
#             return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SignInView(APIView):
#
#     def post(self, request: Request) -> Response:
#         serializer = SignInSerializer(data=request.data)
#         if serializer.is_valid():
#             username = serializer.data['username']
#             password = serializer.data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return Response(status=status.HTTP_201_CREATED)
#             return Response(status=status.HTTP_403_FORBIDDEN)


# class SignInView(APIView):
#     def post(self, request):
#         serializer = SignInSerializer(data=request.data)
#         # serializer_data = list(request.POST.keys())[0]
#         if serializer.is_valid():
#             user_data = json.loads(serializer.data)
#             username = user_data.get('username')
#             password = user_data.get('password')
#             try:
#                 user = authenticate(request, username=username, password=password)
#                 if user is not None:
#                     login(request, user)
#                     return Response(status=status.HTTP_201_CREATED)
#             except Exception:
#                 return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SignUpView(CreateAPIView):
#     """
#     Регистрация, работает 1
#     """
#     queryset = User.objects.all()
#     serializer_class = SignUpSerializer

# class SignUpView(APIView):
#     """
#     регистрация ии 1, работает в рест, не работает во фронте, возможно 'name' это не 'first_name'
#     """
#     def post(self, request):
#         serializer = SignUpSerializer(data=request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data.get('username')
#             password = serializer.validated_data.get('password')
#             name = serializer.validated_data.get('first_name')
#
#             if User.objects.filter(username=username).exists():
#                 return Response({'error': 'Пользователь с таким именем пользователя уже существует'})
#
#             user = User.objects.create_user(username=username, password=password, first_name=name)
#             return Response({'message': 'Пользователь успешно зарегистрирован'})
#
#         return Response(serializer.errors)


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


class SignOutView(APIView):
    """
    Выход
    """

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Смена пароля, работает
    """

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
    serializer_class = ProfileAvatarSerializer

    def post(self, request, *args, **kwargs):
        instance = request.user.shop_profile_user
        serializer = self.serializer_class(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
