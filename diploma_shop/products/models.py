# from datetime import datetime
import datetime

from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.context_processors import auth
from django.contrib.auth.models import User
from PIL import Image
from django.utils import timezone
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Category(models.Model):
    """
    Модель категорий продуктов
    """
    title = models.CharField(max_length=200, db_index=True, verbose_name='Название категории продукта')
    description = models.TextField(blank=True, verbose_name='Описание категории продукта')
    # slug = models.SlugField(max_length=200, db_index=True, unique=True, verbose_name='URL категории продукта')
    # thumbnail = models.ImageField(
    #     blank=True,
    #     upload_to='images/thumbnails/',
    #     default='images/no_image.jpg',
    #     validators=[FileExtensionValidator(allowed_extensions=('png', 'jpg', 'webp', 'jpeg', 'gif'))],
    #     verbose_name='Превью категории продукта'
    # )
    image = models.ForeignKey(
        'CategoryImages',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="image",
        verbose_name='Изображение категории'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subcategories",
        verbose_name='Родительская категория'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Категория продукта'
        verbose_name_plural = 'Категории продукта'

    def __str__(self):
        return self.title


# class ProductType(models.Model):
#     """
#     Модель типа продукта для магазина
#     """
#     name = models.CharField(max_length=200, db_index=True, verbose_name=_('product type name'))
#     slug = models.SlugField(max_length=200, db_index=True, unique=True, verbose_name=_('product Type URL'))
#     category_product = models.ForeignKey(
#         'ProductCategory',
#         on_delete=models.PROTECT,
#         default=True,
#         related_name='product_category_product_type',
#         verbose_name=_('product category')
#     )
#
#     # property_type_product = models.ForeignKey(
#     #     'PropertyTypeProduct',
#     #     on_delete=models.PROTECT,
#     #     default=True,
#     #     related_name='shop_property_type_product_type',
#     #     verbose_name="Тип характеристики продукта"
#     # )
#
#     class Meta:
#         ordering = ('category_product',)
#         verbose_name = _('type of product')
#         verbose_name_plural = _('product types')
#
#     def __str__(self):
#         return self.name


class ProductInstance(models.Model):
    """
    Модель конкретного продукта для магазина
    """
    title = models.CharField(max_length=200, db_index=True, verbose_name='Название продукта')
    slug = models.SlugField(max_length=200, unique=True, db_index=True, verbose_name='URL продукта')
    item_number = models.IntegerField(default=True, verbose_name='Артикул продукта')
    description = models.TextField(blank=True, max_length=500, verbose_name='Краткое описание продукта')
    fullDescription = models.TextField(blank=True, verbose_name='Полное описание продукта')
    freeDelivery = models.BooleanField(default=False, verbose_name='free delivery')

    sort_index = models.PositiveIntegerField(default=True, verbose_name='Индекс сортировки')
    number_of_purchases = models.PositiveIntegerField(default=True, verbose_name='Количество покупок')
    limited_edition = models.BooleanField(default=False, null=True, verbose_name='Ограниченный тираж')

    price = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена продукта'
    )
    salePrice = models.DecimalField(
        null=True,
        blank=True,
        default=0,
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена продукта при распродаже'
    )
    # thumbnail = models.ImageField(
    #     blank=True,
    #     upload_to='images/thumbnails/',
    #     default='images/no_image.jpg',
    #     validators=[FileExtensionValidator(allowed_extensions=('png', 'jpg', 'webp', 'jpeg', 'gif'))],
    #     verbose_name='Превью продукта'
    # )
    count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Количество продукта на складе')
    available = models.BooleanField(default=True, null=True, verbose_name='Доступность продукта в каталоге')

    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания продукта')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменения продукта')

    dateFrom = models.DateTimeField(default=timezone.now, verbose_name='Дата начала распродажи продукта')
    dateTo = models.DateTimeField(default=timezone.now, verbose_name='Дата окончания распродажи продукта')

    archived = models.BooleanField(default=True, verbose_name='Продукт архивирован')
    tags = models.ManyToManyField(
        'Tag',
        related_name='tag',
        verbose_name='Теги продукта'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="product_category",
        verbose_name="Категория продукта",
    )

    rating = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=1,
        verbose_name='Рейтинг продукта'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # return reverse('product_detail', kwargs={'slug': self.slug})
        return reverse('product_detail', kwargs={"pk": self.pk})

    def get_review(self):
        return self.reviews_set.filter(parent__isnull=True)

    class Meta:
        ordering = ('title',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        indexes = [models.Index(fields=['id', 'slug'])]


class PropertyTypeProduct(models.Model):
    """
    Модель названия характеристики продукта
    """
    name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Название характеристики продукта'
    )
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        unique=False,
        verbose_name='URL характеристики продукта'
    )
    category = models.ManyToManyField(
        'Category',
        related_name='propertyType_category',
        verbose_name='Категория продукта'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Название характеристики продукта'
        verbose_name_plural = 'Названия характеристик продукта'

    def __str__(self):
        return self.name


class PropertyInstanceProduct(models.Model):
    """
    Модель значения характеристики конкретного продукта
    """
    value = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Значение характеристики'
    )
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        unique=False,
        verbose_name='URL значения характеристики'
    )
    product = models.ForeignKey(
        'ProductInstance',
        default=None,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='specifications',
        verbose_name='Продукт'
    )
    name = models.ForeignKey(
        'PropertyTypeProduct',
        default=None,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='propertyInstance_propertyType',
        verbose_name='Название характеристики продукта'
    )

    class Meta:
        ordering = ('value',)
        verbose_name = 'Значение характеристики продукта'
        verbose_name_plural = 'Значения характеристик продуктов'

    def __str__(self):
        return self.value


class ProductImages(models.Model):
    """
    Модель изображения для магазина
    """
    # title = models.CharField(
    #     max_length=150,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     verbose_name='Описание изображения'
    # )
    src = models.ImageField(
        upload_to='images/images_product/',
        default='images/no_image.jpg',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    alt = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        default=None,
        verbose_name='Альтернативная строка изображения продукта'
    )
    product = models.ForeignKey(
        'ProductInstance',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name='images',
        verbose_name='Продукт'
    )

    def __str__(self):
        return f'{self.product}'

    class Meta:
        verbose_name = 'Изображение продукта'
        verbose_name_plural = 'Изображения продуктов'

    @property
    def photo_url(self):
        if self.src and hasattr(self.src, 'url'):
            return self.src.url

    def save(self, *args, **kwargs):
        super().save()
        img = Image.open(self.src.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.src.path)


class CategoryImages(models.Model):
    """
    Модель изображения для магазина
    """
    # title = models.CharField(
    #     max_length=150,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     verbose_name='Описание изображения'
    # )
    src = models.ImageField(
        upload_to='images/images_product/',
        default='images/no_image.jpg',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    alt = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        default=None,
        verbose_name='Альтернативная строка изображения продукта'
    )

    def __str__(self):
        return f'{self.alt}'

    class Meta:
        verbose_name = 'Изображение категории'
        verbose_name_plural = 'Изображения категорий'

    @property
    def photo_url(self):
        if self.src and hasattr(self.src, 'url'):
            return self.src.url

    def save(self, *args, **kwargs):
        super().save()
        img = Image.open(self.src.path)
        if img.height > 25 or img.width > 25:
            output_size = (25, 25)
            img.thumbnail(output_size)
            img.save(self.src.path)


class AvatarsImages(models.Model):
    """
    Модель изображения для аватарок
    """
    src = models.ImageField(
        upload_to='images/images_avatars/',
        default='images/no_image.jpg',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    # alt = models.CharField(max_length=255, null=True, blank=True)
    # title = models.CharField(
    #     max_length=150,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     verbose_name='Описание изображения'
    # )
    # src = models.ImageField(
    #     upload_to='images/images_avatars/',
    #     default='images/no_image.jpg',
    #     blank=True,
    #     null=True,
    #     verbose_name='Изображение'
    # )
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


class Rate(models.Model):
    """
    Значение рейтинга
    """
    value = models.SmallIntegerField(
        default=0,
        verbose_name='Значение'
    )

    class Meta:
        ordering = ('value',)
        verbose_name = 'Значение рейтинга'
        verbose_name_plural = 'Значения рейтинга'

    def __str__(self):
        return f'{self.value}'
        # return self.value


class Review(models.Model):
    """
    Модель отзывов к продуктам
    """

    author = models.ForeignKey(
        # User,
        to=User,
        on_delete=models.CASCADE,
        default=None,
        # null=True,
        # blank=True,
        related_name='author_review',
        verbose_name='Автор отзыва'
    )

    rate = models.ForeignKey(
        'Rate',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="review",
        verbose_name='Значение рейтинга'
    )
    text = models.TextField(blank=True, max_length=5000, verbose_name='Текст отзыва')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания отзыва')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменения отзыва')
    product = models.ForeignKey(
        'ProductInstance',
        default=None,
        # null=True,
        # blank=True,
        on_delete=models.CASCADE,
        # related_name='product_review',
        related_name='reviews',
        verbose_name='Продукт'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        # related_name="reviews_parent",
        related_name="children_review",
        verbose_name='Родительский отзыв'
    )
    active = models.BooleanField(default=True, verbose_name='Активный')

    def __str__(self):
        return f'{self.author} - {self.product}'
        # return 'Comment by {} on {}'.format(self.name, self.post)

    class Meta:
        verbose_name = 'Отзыв к продукту'
        verbose_name_plural = 'Отзывы к продукту'
        ordering = ('-date',)


class Tag(models.Model):
    """
    Тег продукта
    """
    name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        default=None,
        verbose_name='Тэг'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Модель профиля пользователя
    """
    user = models.OneToOneField(
        # User,
        to=User,
        on_delete=models.CASCADE,
        related_name='shop_profile_user',
        verbose_name='Пользователь'
    )
    # slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name='URL пользователя')
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
    # avatar = models.ImageField(
    #     upload_to='images/images_avatars/',
    #     default='images/no_image.jpg',
    #     blank=True,
    #     null=True,
    #     validators=[FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg'))],
    #     verbose_name='Аватар пользователя'
    # )
    avatar = models.ForeignKey(
        'AvatarsImages',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="profile",
        verbose_name='Аватар пользователя'
    )
    # email = models.EmailField(max_length=50, unique=True, blank=True, default=None, verbose_name='Email')
    phone = PhoneNumberField(unique=True, null=True, blank=True, default=None, verbose_name='Номер телефона')

    class Meta:
        """
        Сортировка, название таблицы в базе данных
        """
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

    # def save(self):
    #     super().save()
    #     img = Image.open(self.avatar.path)
    #     if img.height > 50 or img.width > 50:
    #         output_size = (50, 50)
    #         img.thumbnail(output_size)
    #         img.save(self.avatar.path)


class PurchaseList(models.Model):
    """
    Модель списка покупок пользователя
    """
    user = models.OneToOneField(
        # User,
        to=User,
        on_delete=models.CASCADE,
        related_name='user_purchase_list',
        verbose_name='user'
    )
    METHOD_PAYMENT = (
        (1, 'карта'),
        (2, 'счёт'),
    )
    METHOD_DELIVERY = (
        (1, 'доставка'),
        (2, 'экспресс-доставка'),
    )
    STATUS_PAYMENT = (
        (1, 'не оплачено'),
        (2, 'оплачено'),
        (3, 'возврат оплаты'),
    )
    STATUS_DELIVERY = (
        (1, 'доставлено'),
        (2, 'доставляется'),
        (3, 'не доставлено'),
        (4, 'возврат продукта'),
    )
    payment_method = models.IntegerField(
        null=True,
        choices=METHOD_PAYMENT,
        default=1,
        verbose_name="Способ оплаты"
    )
    delivery_method = models.IntegerField(
        null=True,
        choices=METHOD_DELIVERY,
        default=1,
        verbose_name="Способ доставки"
    )
    payment_status = models.IntegerField(
        null=True,
        choices=STATUS_PAYMENT,
        default=1,
        verbose_name="Статус оплаты"
    )
    delivery_status = models.IntegerField(
        null=True,
        choices=STATUS_DELIVERY,
        default=1,
        verbose_name="Статус доставки"
    )
    time_create = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('purchase time')
    )
    price = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость заказа'
    )
    error_text = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
        default=None,
        verbose_name='Текст ошибки'
    )
    product = models.ManyToManyField(
        'ProductInstance',
        related_name=_('product'),
        verbose_name="Продукт"
    )
    slug = models.SlugField(
        max_length=255,
        default='purchase',
        db_index=True,
        verbose_name='URL истории покупок'
    )

    class Meta:
        ordering = ('time_create',)
        verbose_name = 'Список покупок пользователя'
        verbose_name_plural = 'Списки покупок пользователей'

    def __str__(self):
        return f' Список покупок пользователя {self.user.username}'


# class SpecialOffer(models.Model):
#     """
#     Модель спецпредложений пользователя
#     """
#     name_special_offer = models.CharField(
#         max_length=100,
#         blank=True,
#         default=None,
#         verbose_name=_('name of the special offer')
#     )
#     description_special_offer = models.TextField(
#         blank=True,
#         default=None,
#         verbose_name=_('name of the special offer')
#     )
#     slug = models.SlugField(max_length=255, default='specialoffer', db_index=True, verbose_name=_('special offer URL'))
#     customer = models.ManyToManyField('Customer', related_name='shop_specialoffer', verbose_name=_('customer'))
#
#     class Meta:
#         verbose_name = _('special offer for the user')
#         verbose_name_plural = _('special offer for the users')
#
#     def __str__(self):
#         return self.name_special_offer


# class Order(models.Model):
#     """
#     Модель параметров заказа
#     """
#     STATUS_CHOICES = (
#         (1, 'waiting_for_payment'),
#         (2, 'paid'),
#         (3, 'shipped'),
#         (4, 'delivered'),
#         (5, 'returned'),
#     )
#     STATUS_CART = (
#         (1, 'in_cart'),
#         (2, 'not_in_cart')
#     )
#
#     customer = models.ForeignKey(
#         'Customer',
#         on_delete=models.CASCADE,
#         related_name='shop_customer_order',
#         verbose_name='Покупатель'
#     )
#     created = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время формирования заказа")
#     updated = models.DateTimeField(auto_now=True, verbose_name="Дата и время изменения заказа")
#     items = models.ManyToManyField(
#         'OrderItem',
#         related_name='shop_items_order',
#         verbose_name="Заказанные продукты"
#     )
#     status = models.IntegerField(
#         null=True,
#         choices=STATUS_CHOICES,
#         default=STATUS_CART,
#         verbose_name="Статус заказа"
#     )
#
#     # payment = models.ForeignKey(Payment, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Оплата")
#
#     def __str__(self):
#         return self.customer.user.username
#
#     class Meta:
#         verbose_name = 'Параметры заказа'
#         verbose_name_plural = 'Параметры заказа'
#         ordering = ['pk']
class Order(models.Model):
    """
    Модель заказа
    """
    STATUS_CHOICES = (
        (1, 'ожидание платежа'),
        (2, 'оплачено'),
        (3, 'отправлено'),
        (4, 'доставлено'),
        (5, 'вернулся'),
    )
    STATUS_CART = (
        (1, 'в корзине'),
        (2, 'не в корзине')
    )

    user = models.OneToOneField(
        # User,
        to=User,
        on_delete=models.CASCADE,
        related_name='user_order',
        verbose_name='Пользователь'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время формирования заказа")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата и время изменения заказа")
    items = models.ManyToManyField(
        'OrderItem',
        related_name='shop_items_order',
        verbose_name="Заказанные продукты"
    )
    status = models.IntegerField(
        null=True,
        choices=STATUS_CHOICES,
        default=STATUS_CART,
        verbose_name="Статус заказа"
    )
    payment = models.ForeignKey(
        'Payment',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Оплата"
    )

    # amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True, verbose_name="Количество")
    # creation_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время формирования заказа")
    # comment = models.TextField(blank=True, null=True, verbose_name="Комментарий к заказу")

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Параметры заказа'
        verbose_name_plural = 'Параметры заказа'
        ordering = ['pk']


class OrderItem(models.Model):
    """
    Модель заказанного продукта
    """
    # order = models.ForeignKey(
    #     'Order',
    #     on_delete=models.CASCADE,
    #     related_name='shop_order_orderitem',
    #     verbose_name="Параметры заказа"
    # )
    product = models.ForeignKey(
        'ProductInstance',
        on_delete=models.CASCADE,
        related_name='shop_product_orderitem',
        verbose_name="Заказанный продукт"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена заказанного продукта с учётом всех акций и скидок"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество заказанного продукта"
    )

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = 'Заказанный продукт'
        verbose_name_plural = 'Заказанные продукты'
        ordering = ['pk']


class Payment(models.Model):
    """
    Модель оплаты заказа
    """
    user = models.ForeignKey(
        # User,
        to=User,
        on_delete=models.CASCADE,
        related_name='user_payment',
        verbose_name='Покупатель'
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время оплаты")
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты"
    )

    def __str__(self):
        return self.user

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['pk']
