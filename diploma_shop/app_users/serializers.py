from rest_framework import serializers
from typing import Optional, Any, List, Union
from .models import *


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User
    """

    class Meta:
        model = User
        fields = ('email',)


class AvatarUploadSerializer(serializers.ModelSerializer):
    """
    Аватар для UpdateAvatarAPIView
    """
    src = serializers.ImageField()

    class Meta:
        model = AvatarsImages
        fields = ('src',)


class ProfileImageSerializer(serializers.ModelSerializer):
    """
    Аватар для ProfileView > ProfileSerializer
    """
    src = serializers.SerializerMethodField()

    class Meta:
        model = AvatarsImages
        fields = ('src', 'alt')

    def get_src(self, obj) -> Optional[str]:
        if obj.src and hasattr(obj.src, 'url'):
            return obj.src.url


class ProfileSerializer(serializers.ModelSerializer):
    """
    Профиль пользователя
    """
    email = serializers.EmailField(
        source='user.email',
        allow_null=True,
        allow_blank=True
    )

    avatar = ProfileImageSerializer(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = (
            'fullName',
            'email',
            'phone',
            'avatar'
        )

    def create(self, validated_data: dict) -> Profile:
        # Извлекаем вложенные данные для аватара и пользователя
        avatar_data = validated_data.get('avatar', None)
        user_data = validated_data.get('user', None)

        # Проверяем существование пользователя в валидированных данных
        if user_data:
            user = User.objects.get(email=user_data.get('email'))
            if not user:
                raise serializers.ValidationError("User does not exist.")
        else:
            raise serializers.ValidationError("User data is required.")

        # Создаем или получаем существующий объект аватара
        if avatar_data:
            avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
            validated_data['avatar'] = avatar

        # Создаем профиль пользователя
        profile, created = Profile.objects.get_or_create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data: dict) -> Profile:
        user_data = validated_data.pop('user', None)
        new_email = validated_data.pop('email', None)
        if user_data:
            email = new_email
            if email and email != instance.user.email:
                instance.user.email = email
                instance.user.save()

        # Обрабатываем остальные поля
        avatar_data = validated_data.pop('avatar', None)
        if avatar_data:
            avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
            instance.avatar = avatar

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class SignUpSerializer(serializers.Serializer):
    """
    Регистрация
    """
    name = serializers.CharField(source='fullName', max_length=50)
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)

    class Meta:
        model = Profile
        fields = [
            'name',
            'username',
            'password'
        ]


class SignInSerializer(serializers.Serializer):
    """
    Вход
    """
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)
