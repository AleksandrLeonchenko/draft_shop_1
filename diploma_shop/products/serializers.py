from rest_framework import serializers
# from rest_framework_recursive.fields import RecursiveField
# from django.contrib.auth.models import Group

from .models import *


class FilterReviewListSerializer(serializers.ListSerializer):
    """Фильтр комментариев, только parents"""

    def to_representation(self, data):
        data = data.filter(parent=None)
        return super().to_representation(data)


class RecursiveSerializer(serializers.Serializer):
    """Вывод рекурсивно children"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class RatingCreateSerializer(serializers.ModelSerializer):
    """
    Добавление отзыва
    """

    class Meta:
        model = Rating
        fields = (
            'rating_value',
            # 'product',
        )

    def create(self, validated_data):
        rating = Rating.objects.update_or_create(
            # ip=validated_data.get('ip', None),
            product=validated_data.get('product', None),
            author=validated_data.get('author', None),
            # rating_value=validated_data.get('rating_value', None),
            defaults={'rating_value': validated_data.get('rating_value')}
        )
        return rating


class RatingSerializer(serializers.ModelSerializer):
    """
    Добавление отзыва
    """
    rating_value = serializers.SlugRelatedField(slug_field='value', read_only=True)

    class Meta:
        model = Rating
        # fields = (
        #     'rating_value',
        #     'product',
        # )
        fields = "__all__"


# class ReviewCreateSerializer(serializers.ModelSerializer):
#     """
#     Добавление отзыва, версия 1
#     """
#
#     class Meta:
#         model = Review
#         fields = "__all__"
#         # exclude = ('product',)
#
#     def create(self, validated_data):
#         review = Review.objects.update_or_create(
#             # ip=validated_data.get('ip', None),
#             product=validated_data.get('product', None),
#             active=validated_data.get('active', None),
#             text=validated_data.get('text', None),
#             defaults={'author': validated_data.get('author'), 'rate': validated_data.get('rate')}
#         )
#         return review


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Добавление отзыва, версия 2
    """

    class Meta:
        model = Review
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    """
    Вывод отзыва, версия 1
    """

    # children_review = RecursiveSerializer(many=True)
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        list_serializer_class = FilterReviewListSerializer
        model = Review
        fields = (
            'author',
            # 'email',
            'date',
            'text',
            'rate',
            # 'product',
            # 'children_review',
        )


class ImageSerializer(serializers.ModelSerializer):
    """
    Вывод изображений продукта
    """

    class Meta:
        model = Images
        # fields = "__all__"
        fields = (
            'src',
            'alt',
        )


class TagsSerializer(serializers.ModelSerializer):
    """
    Вывод тегов продукта
    """

    class Meta:
        model = Tags
        fields = "__all__"
        # fields = (
        #     'id',
        #     'name',
        # )


class CategorySerializer(serializers.ModelSerializer):
    """
    Вывод категорий продукта
    """
    subcategories = RecursiveSerializer(many=True)
    image = ImageSerializer(many=True)

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
    tags = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    reviews = ReviewSerializer(many=True)
    images = ImageSerializer(many=True)

    # rating_user = serializers.BooleanField()
    # middle_star = serializers.IntegerField()

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
            'full_description',
            'free_delivery',
            'images',
            'tags',
            'reviews',
            'rating',
        )


class PropertyTypeProductSerializer(serializers.ModelSerializer):
    """
    Вывод названий характеристик продукта
    """

    # children_review = RecursiveSerializer(many=True)
    # author = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        # list_serializer_class = FilterReviewListSerializer
        model = PropertyTypeProduct
        fields = (
            'category',
            # 'email',
            # 'date',
            'name',
            # 'rate',
            # 'rate_review',
            # 'xxx',
            'product',
            # 'children_review',
            # 'rating_user2',
            # 'product_review',
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


class ProductLimitedSerializer(serializers.ModelSerializer):
    reviews_count = serializers.IntegerField()

    # class Meta:
    #     model = ProductInstance
    #     # exclude = ('available',)
    #     fields = (
    #         'id',
    #         'category',
    #         'price',
    #         'count',
    #         'date',
    #         'title',
    #         'description',
    #         'full_description',
    #         'free_delivery',
    #         'images',
    #         'tags',
    #         # 'available',
    #         # 'archived',
    #         'reviews',
    #         # 'rating_user',
    #         # 'middle_star',
    #         'specifications',
    #         'rating',
    #         # 'product_rating',
    #     )
    class Meta:
        model = ProductInstance
        fields = (
            'id',
            # 'title',
            # 'item_number',
            'free_delivery',
            'price',
            'count',
            'available',
            'archived',
            'category',
            # 'reviews',
            'reviews_count',
            'date',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='title', read_only=True)
    tags = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    reviews = ReviewSerializer(many=True)
    images = ImageSerializer(many=True)
    specifications = PropertyInstanceProductSerializer(many=True)

    # product_rating = RatingSerializer(many=True)

    # tags = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)

    # rating_user = serializers.BooleanField()
    # middle_star = serializers.IntegerField()

    class Meta:
        model = ProductInstance
        # exclude = ('available',)
        fields = (
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'full_description',
            'free_delivery',
            'images',
            'tags',
            # 'available',
            # 'archived',
            'reviews',
            # 'rating_user',
            # 'middle_star',
            'specifications',
            'rating',
            # 'product_rating',
        )


# class RatingCreateSerializer(serializers.ModelSerializer):
#     """
#     Добавление отзыва
#     """
#
#     class Meta:
#         model = Rating
#         fields = (
#             'rate',
#             'product',
#         )
#
#     def create(self, validated_data):
#         rating = Rating.objects.update_or_create(
#             ip=validated_data.get('ip', None),
#             product=validated_data.get('product', None),
#             author=validated_data.get('author', None),
#             defaults={'rate': validated_data.get('rate')}
#         )
#         return rating


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            'id',
            'created',
            'updated',
            'user',
            'status'
            'payment',
        )

# class GroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ('pk', 'name')
