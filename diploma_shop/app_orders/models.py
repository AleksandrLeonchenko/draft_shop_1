# from datetime import datetime
# import datetime
# from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.db.models import Sum, F, Count
# from django.core.exceptions import ValidationError
# from django.core.validators import FileExtensionValidator
from django.db import models
# from django.contrib.auth.context_processors import auth
# from django.contrib.auth.models import User
from PIL import Image
# from django.utils import timezone
# from django.urls import reverse
# from phonenumber_field.modelfields import PhoneNumberField
# from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Basket(models.Model):
    """
    Модель корзины
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='basket2',
        verbose_name='Пользователь'
    )

    products = models.ManyToManyField(
        'app_products.ProductInstance',
        through='BasketItem',
        verbose_name='Выбранные товары'
    )

    totalCost = models.FloatField(
        blank=True,
        null=True,
        # default=0
    )  # Можно удалить

    def __str__(self):
        return f'{self.user}'

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ['id']


class BasketItem(models.Model):
    """
    Модель продукта в корзине
    """
    basket = models.ForeignKey(
        'Basket',
        on_delete=models.CASCADE,
        # related_name='products',
        related_name='items2',
        verbose_name='Корзина'
    )
    product = models.ForeignKey(
        'app_products.ProductInstance',
        on_delete=models.CASCADE,
        related_name='product_basketitem2',
        verbose_name='Товар'
    )
    count = models.PositiveIntegerField(verbose_name='Количество')

    def __str__(self):
        return f'{self.product} ({self.count} шт.)'

    class Meta:
        verbose_name = 'Продукт в корзине'
        verbose_name_plural = 'Продукты в корзине'
        ordering = ['id']


class Order(models.Model):  # нужно будет убрать поле profile из модели, всё равно у basket есть user
    """
    Модель заказа
    """
    DELIVERY_CHOICES = (
        (1, 'Доставка'),
        (2, 'Экспресс-доставка'),
    )
    PAYMENT_CHOICES = (
        (1, 'Онлайн картой'),
        (2, 'Онлайн со случайного чужого счёта'),
    )
    STATUS_CHOICES = (
        (1, 'ожидание платежа'),
        (2, 'оплачено'),
    )
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время формирования заказа")
    deliveryType = models.IntegerField(
        null=True,
        choices=DELIVERY_CHOICES,
        default=1,
        verbose_name="Способ доставки"
    )
    paymentType = models.IntegerField(
        null=True,
        choices=PAYMENT_CHOICES,
        default=1,
        verbose_name="Способ оплаты"
    )
    totalCost = models.FloatField(default=1)
    status = models.IntegerField(
        null=True,
        choices=STATUS_CHOICES,
        default=1,
        verbose_name="Статус заказа"
    )
    city = models.CharField(max_length=100, default='yyy')
    address = models.CharField(max_length=100, default='xxx')
    basket = models.OneToOneField(
        'Basket',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Корзина'
    )

    def __str__(self):
        # return f'{self.basket.user.username}'
        return self.address

    def calculate_total_cost(self):
        # total_cost = 777
        total_cost = 0
        basket_items = self.basket.items2.all()  # Получаем все элементы в корзине
        for basket_item in basket_items:
            total_cost += basket_item.product.price * basket_item.count  # Суммируем стоимость каждого продукта в корзине
        return total_cost

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['pk']


class PaymentCard(models.Model):
    """
    Модель карты оплаты
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cards2',
        verbose_name='Владелец',
    )
    number = models.CharField(
        unique=True,
        max_length=8,
        verbose_name='Номер карты',
    )
    name = models.CharField(
        max_length=30,
        verbose_name='Имя',
    )
    month = models.CharField(
        max_length=2,
        verbose_name='Месяц',
    )
    year = models.CharField(
        max_length=4,
        verbose_name='Год',
    )
    code = models.CharField(
        max_length=3,
        verbose_name='Код',
    )

    def __str__(self):
        # return f'{self.owner}'
        return f'{self.owner} - {self.name}'

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['pk']
