from django.contrib.auth import get_user_model
from django.db import models
from PIL import Image
from django.db.models import Sum, F, Count, Avg, ExpressionWrapper, fields
from django.db.models.functions import Round
from django.utils import timezone
from django.urls import reverse
from typing import List, Optional, Union

User = get_user_model()


class ProductInstanceManager(models.Manager):
    def filter_and_annotate(self, product_ids: Optional[List[int]] = None) -> models.QuerySet:
        if product_ids is not None:
            queryset = self.filter(id__in=product_ids, available=True)
        else:
            queryset = self.filter(available=True)
        return queryset.annotate(
            reviews_count=Count('reviews2'),
            average_rating=ExpressionWrapper(
                Round(Avg('reviews2__rate__value') * 10) / 10.0,
                output_field=fields.DecimalField()
            )
        )


class Category(models.Model):
    """
    Модель категорий продуктов
    """
    title = models.CharField(max_length=200, db_index=True, verbose_name='Название категории продукта')
    description = models.TextField(blank=True, verbose_name='Описание категории продукта')
    image = models.ForeignKey(
        'CategoryImages',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="image2",
        verbose_name='Изображение категории'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subcategories2",
        verbose_name='Родительская категория'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Категория продукта'
        verbose_name_plural = 'Категории продукта'

    def __str__(self):
        return self.title


class ProductInstance(models.Model):
    """
    Модель конкретного продукта для магазина
    """
    objects = ProductInstanceManager()

    title = models.CharField(max_length=200, db_index=True, verbose_name='Название продукта')
    slug = models.SlugField(max_length=200, unique=True, db_index=True, verbose_name='URL продукта')
    item_number = models.IntegerField(default=True, verbose_name='Артикул продукта')
    description = models.TextField(blank=True, max_length=500, verbose_name='Краткое описание продукта')
    fullDescription = models.TextField(blank=True, verbose_name='Полное описание продукта')
    freeDelivery = models.BooleanField(default=False, verbose_name='free delivery')
    sort_index = models.PositiveIntegerField(default=True, verbose_name='Индекс сортировки')
    number_of_purchases = models.PositiveIntegerField(
        default=True,
        null=True,
        blank=True,
        verbose_name='Количество покупок'
    )
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

    count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Количество продукта на складе')
    available = models.BooleanField(default=True, null=True, verbose_name='Доступность продукта в каталоге')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания продукта')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменения продукта')
    dateFrom = models.DateTimeField(default=timezone.now, verbose_name='Дата начала распродажи продукта')
    dateTo = models.DateTimeField(default=timezone.now, verbose_name='Дата окончания распродажи продукта')
    archived = models.BooleanField(default=True, verbose_name='Продукт архивирован')
    tags = models.ManyToManyField(
        'Tag',
        related_name='tag2',
        verbose_name='Теги продукта'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="product_category2",
        verbose_name="Категория продукта",
    )
    rating = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=1,
        verbose_name='Рейтинг продукта'
    )
    order = models.ForeignKey(
        'app_orders.Order',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='products2'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('product_detail', kwargs={"pk": self.pk})

    def get_review(self) -> models.QuerySet:
        return self.reviews_set.filter(parent__isnull=True)

    class Meta:
        ordering = ('date',)
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
        related_name='propertyType_category2',
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
        related_name='specifications2',
        verbose_name='Продукт'
    )
    name = models.ForeignKey(
        'PropertyTypeProduct',
        default=None,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='propertyInstance_propertyType2',
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
        related_name='images2',
        verbose_name='Продукт'
    )

    def __str__(self):
        return f'{self.product}'

    class Meta:
        verbose_name = 'Изображение продукта'
        verbose_name_plural = 'Изображения продуктов'

    @property
    def photo_url(self) -> Optional[str]:
        if self.src and hasattr(self.src, 'url'):
            return self.src.url

    def save(self, *args, **kwargs) -> None:
        super().save()
        img = Image.open(self.src.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.src.path)


class CategoryImages(models.Model):
    """
    Модель изображения для категории
    """

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

    def __str__(self) -> str:
        return f'{self.alt}'

    class Meta:
        verbose_name = 'Изображение категории'
        verbose_name_plural = 'Изображения категорий'

    @property
    def photo_url(self) -> Optional[str]:
        if self.src and hasattr(self.src, 'url'):
            return self.src.url

    def save(self, *args, **kwargs) -> None:
        super().save()
        img = Image.open(self.src.path)
        if img.height > 25 or img.width > 25:
            output_size = (25, 25)
            img.thumbnail(output_size)
            img.save(self.src.path)


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

    def __str__(self) -> str:
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
        related_name='author_review2',
        verbose_name='Автор отзыва'
    )

    rate = models.ForeignKey(
        'Rate',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="review2",
        verbose_name='Значение рейтинга'
    )
    text = models.TextField(blank=True, max_length=5000, verbose_name='Текст отзыва')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания отзыва')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменения отзыва')
    product = models.ForeignKey(
        'ProductInstance',
        default=None,
        on_delete=models.CASCADE,
        related_name='reviews2',
        verbose_name='Продукт'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children_review2",
        verbose_name='Родительский отзыв'
    )
    active = models.BooleanField(default=True, verbose_name='Активный')

    def __str__(self) -> str:
        return f'{self.author} - {self.product}'

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
