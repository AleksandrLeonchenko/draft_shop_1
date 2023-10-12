# import json
# import django_filters
# from django.db import connection
# from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
# from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser
from rest_framework.parsers import MultiPartParser, FormParser
# from django.db import models, transaction
# from django.db.models import Avg, Case, When, Sum, Count, Prefetch, Q
# from django.shortcuts import get_object_or_404
# from rest_framework import status, generics, filters
from rest_framework import status
# from django.contrib.auth.models import Group
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.authentication import SessionAuthentication
# from rest_framework.decorators import parser_classes
# from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.request import Request
# from rest_framework.response import Response
from rest_framework.views import APIView
# from django_filters import rest_framework as filters
# from django_filters import FilterSet, CharFilter, NumberFilter, BooleanFilter, ChoiceFilter
# from django.core.cache import cache
# from pdb import set_trace

# from .forms import BasketDeleteForm
from .serializers import *
# from .models import *
from .service import *


class ProfileView(APIView):
    """
    Отображение, добавление и изменение профиля пользователя
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = ProfileSerializer

    # serializer = ProfileSerializer

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except ObjectDoesNotExist:
            profile = Profile.objects.create(user=request.user)
        serializer = self.serializer_class(profile)
        return Response(serializer.data)

    def post(self, request):  # этот вроде работает
        try:
            # profile = Profile.objects.get(user=request.user)
            profile, created = Profile.objects.get_or_create(user=request.user)
            serializer = self.serializer_class(profile, data=request.data, partial=True)
        except ObjectDoesNotExist:
            serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, email=request.data['email'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    serializer_class = SignInSerializer

    def post(self, request):  # работает!
        try:
            # Пытаемся прочитать данные как JSON
            data = json.loads(list(request.POST.keys())[0])
        except (json.JSONDecodeError, IndexError):
            # Если это не удается, принимаем данные как обычные форменные данные
            data = request.POST.dict()
            data.pop('csrfmiddlewaretoken', None)  # Удалите csrfmiddlewaretoken

        serializer = SignInSerializer(data=data)

        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            user = authenticate(username=username, password=password)
            if user.is_authenticated:
                # request.session.flush()  # Очистка сессии
                login(request, user)
                # cache.clear()
                return Response({"message": "successful operation"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """
    Регистрация
    """
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    User = get_user_model()
    serializer_class = SignUpSerializer

    def post(self, request):  # с фронта работает

        try:
            # Пытаемся прочитать данные как JSON
            data = json.loads(list(request.POST.keys())[0])
        except (json.JSONDecodeError, IndexError):
            # Если это не удается, принимаем данные как обычные форменные данные
            data = request.POST.dict()
            data.pop('csrfmiddlewaretoken', None)  # Удаляем csrfmiddlewaretoken

        serializer = SignUpSerializer(data=data)
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

        return Response({"error": "unsuccessful operation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SignOutView(APIView):
    """
    Выход из системы
    """
    # permission_classes = (AllowAny,)
    authentication_classes = [SessionAuthentication]

    # authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request):
        logout(request)
        # request.session.flush()  # Очистка сессии
        # cache.clear()
        return Response({"message": "successful operation"}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """
    Смена пароля
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    # permission_classes = [AllowAny]

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
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AvatarUploadSerializer
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        # Создаем промежуточный словарь
        if request.data.get('avatar'):
            data = {
                'src': request.data.get('avatar')
            }
        else:
            data = {
                'src': request.data.get('src')
            }

        profile, _ = Profile.objects.get_or_create(user=request.user)
        if profile.avatar:
            file_serializer = AvatarUploadSerializer(instance=profile.avatar, data=data)  # Используем data
        else:
            file_serializer = AvatarUploadSerializer(data=data)  # Используем data
        if file_serializer.is_valid():
            avatar_instance = file_serializer.save()  # Сохраняем экземпляр AvatarsImages
            if not avatar_instance.alt:  # Проверка на отсутствие значения в поле alt
                avatar_instance.alt = avatar_instance.src.name.split('/')[-1].split('.')[0]
                avatar_instance.save()
            profile.avatar = avatar_instance  # Присваиваем профилю корректный экземпляр
            profile.save()  # Сохраняем профиль
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)