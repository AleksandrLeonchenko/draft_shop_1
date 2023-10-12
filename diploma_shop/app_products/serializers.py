
from rest_framework import serializers, request, exceptions

from .models import *


class FilterReviewListSerializer(serializers.ListSerializer):
    """Фильтр комментариев комментариев, (parents), можно удалить"""

    def to_representation(self, data):
        data = data.filter(parent=None)
        return super().to_representation(data)


class RecursiveSerializer(serializers.Serializer):
    """Для рекурсивного вывода категорий, если понадобится"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Добавление отзыва
    """

    class Meta:
        model = Review
        fields = (
            'text',
            'rate',
        )

    def create(self, validated_data):
        review = Review.objects.update_or_create(
            product=validated_data.get('product', None),
            author=validated_data.get('author', None),
            text=validated_data.get('text', None),
            rate=validated_data.get('rate', None),
            defaults={'rate': validated_data.get('rate')}
        )

        return review


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User
    """

    class Meta:
        model = User
        fields = ('email',)


class ReviewSerializer(serializers.ModelSerializer):
    """
    Вывод отзыва
    """
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)
    date = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    email = serializers.SerializerMethodField()

    def get_email(self, obj):
        return obj.author.email

    class Meta:
        model = Review
        fields = (
            'author',
            'email',
            'date',
            'text',
            'rate',
        )


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Вывод изображений продукта
    """

    class Meta:
        model = ProductImages
        # fields = "__all__"
        fields = (
            'src',
            'alt',
        )


class CategoryImageSerializer(serializers.ModelSerializer):
    """
    Вывод изображений категории
    """

    class Meta:
        model = CategoryImages
        # fields = "__all__"
        fields = (
            'src',
            'alt',
        )


class TagSerializer(serializers.ModelSerializer):
    """
    Вывод тегов продукта
    """

    class Meta:
        model = Tag
        fields = (
            # 'id',
            'name',
        )


class CategorySerializer(serializers.ModelSerializer):
    """
    Вывод категорий продукта
    """
    subcategories = RecursiveSerializer(source='subcategories2', many=True, read_only=True)
    image = CategoryImageSerializer()

    class Meta:
        list_serializer_class = FilterReviewListSerializer
        model = Category
        # fields = "__all__"
        fields = (
            'id',
            'title',
            'image',
            'subcategories',
        )


class ProductListSerializer(serializers.ModelSerializer):
    """
    Список продуктов
    """
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(source='images2', many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    rating = serializers.FloatField(source='average_rating', read_only=True)
    date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')

    class Meta:
        model = ProductInstance
        fields = (
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'freeDelivery',
            'images',
            'tags',
            'reviews',
            'rating',
        )


class ProductSalesSerializer(serializers.ModelSerializer):
    """
    Список продуктов для распродажи
    """
    images = ProductImageSerializer(source='images2', many=True, read_only=True)
    id = serializers.SlugField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    salePrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    dateFrom = serializers.SerializerMethodField()
    dateTo = serializers.SerializerMethodField()

    def get_dateFrom(self, obj):
        return obj.dateFrom.strftime("%m-%d")

    def get_dateTo(self, obj):
        return obj.dateTo.strftime("%m-%d")

    class Meta:
        model = ProductInstance
        fields = (
            'id',
            'price',
            'salePrice',
            'dateFrom',
            'dateTo',
            'title',
            'images',
        )


class PropertyTypeProductSerializer(serializers.ModelSerializer):
    """
    Вывод названий характеристик продукта
    """

    class Meta:
        model = PropertyTypeProduct
        fields = (
            'category',
            'name',
            'product',
        )


class PropertyInstanceProductSerializer(serializers.ModelSerializer):
    """
    Вывод значений характеристик конкретного продукта
    """

    name = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = PropertyInstanceProduct
        fields = (
            'name',
            'value',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Вывод конкретного продукта
    """
    tags = TagSerializer(many=True)
    reviews = ReviewSerializer(source='reviews2', many=True)
    images = ProductImageSerializer(source='images2', many=True, read_only=True)
    specifications = PropertyInstanceProductSerializer(source='specifications2', many=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)
    date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')

    class Meta:
        model = ProductInstance
        fields = (
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'fullDescription',
            'freeDelivery',
            'images',
            'tags',
            'reviews',
            'specifications',
            'rating',
        )
