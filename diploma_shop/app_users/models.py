# from datetime import datetime
# import datetime

from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
# from django.core.validators import FileExtensionValidator
from django.db import models
# from django.contrib.auth.context_processors import auth
# from django.contrib.auth.models import User
from PIL import Image
# from django.db.models import Sum, F, Count
# from django.utils import timezone
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

# from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AvatarsImages(models.Model):
    """
    Модель изображения для аватарок
    """
    src = models.ImageField(
        upload_to='images/images_avatars/',
        default='images/no_image.jpeg',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    # src = models.URLField(
    #     max_length=200,
    #     default='images/no_image.jpeg',
    #     blank=True,
    #     null=True,
    #     verbose_name='Изображение'
    # )  # Изменено на URLField
    alt = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        verbose_name='Альтернативная строка изображения аватара'
    )

    def __str__(self):
        return f'{self.alt}'

    class Meta:
        verbose_name = 'Изображение аватара'
        verbose_name_plural = 'Изображения аватара'

    def get_absolute_url(self):
        return self.src.url

    @property
    def photo_url(self):
        if self.src and hasattr(self.src, 'url'):
            return self.src.url

    def save(self, *args, **kwargs):
        super().save()
        img = Image.open(self.src.path)
        if img.height > 50 or img.width > 50:
            output_size = (50, 50)
            img.thumbnail(output_size)
            img.save(self.src.path)
        # Проверка размера изображения
        MAX_SIZE = 2 * 1024 * 1024  # 2 МБ
        if self.src.size > MAX_SIZE:
            raise ValidationError('Размер изображения должен быть не более 2 МБ.')


class Profile(models.Model):
    """
    Модель профиля пользователя
    """
    user = models.OneToOneField(
        # User,
        to=User,
        on_delete=models.CASCADE,
        # related_name='shop_profile_user',
        related_name='profile2',
        verbose_name='Пользователь'
    )
    slug = AutoSlugField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        verbose_name='URL пользователя'
    )
    fullName = models.CharField(
        max_length=150,
        # blank=True,
        blank=False,
        null=True,
        default=None,
        verbose_name='Ф.И.О.'
    )
    avatar = models.ForeignKey(
        'AvatarsImages',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="profile2",
        verbose_name='Аватар пользователя'
    )
    phone = PhoneNumberField(unique=True, null=True, blank=True, default=None, verbose_name='Номер телефона')

    class Meta:
        ordering = ('user',)
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def get_absolute_url(self):
        """
        Ссылка на профиль
        """
        return reverse('profile', kwargs={'slug': self.slug})

    @property
    def photo_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url

    def __str__(self):
        return f'{self.user.username} (Profile)'
