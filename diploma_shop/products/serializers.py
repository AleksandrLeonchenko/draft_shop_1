from django.db.models import Count
from django.utils import formats
from rest_framework import serializers, request
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta
from django.contrib.auth import authenticate

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


# class RatingCreateSerializer(serializers.ModelSerializer):
#     """
#     Добавление отзыва
#     """
#
#     class Meta:
#         model = Rating
#         fields = (
#             'rating_value',
#             # 'product',
#         )
#
#     def create(self, validated_data):
#         rating = Rating.objects.update_or_create(
#             # ip=validated_data.get('ip', None),
#             product=validated_data.get('product', None),
#             author=validated_data.get('author', None),
#             # rating_value=validated_data.get('rating_value', None),
#             defaults={'rating_value': validated_data.get('rating_value')}
#         )
#         return rating


# class RatingSerializer(serializers.ModelSerializer):
#     """
#     Добавление отзыва
#     """
#     rating_value = serializers.SlugRelatedField(slug_field='value', read_only=True)
#
#     class Meta:
#         model = Rating
#         # fields = (
#         #     'rating_value',
#         #     'product',
#         # )
#         fields = "__all__"


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
        # fields = "__all__"
        fields = (
            # 'author',
            # 'email',
            # 'date',
            'text',
            'rate',
            # 'product',
            # 'children_review',
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


# class UserSerializer(serializers.ModelSerializer):
#
#
#     class Meta:
#         model = User
#         # fields = "__all__"
#         fields = (
#             'id',
#             'email',
#             'username',
#             'first_name',
#         )
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email',)


class ReviewSerializer(serializers.ModelSerializer):
    """
    Вывод отзыва, версия 1
    """

    # queryset = ProductInstance.objects.filter(available=True).annotate(reviews1=Count('reviews'))
    # children_review = RecursiveSerializer(many=True)
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)

    # author = serializers.SlugRelatedField(slug_field='email', read_only=True)
    # email = UserSerializer(many=True)
    # email1 = serializers.EmailField(source='email')

    class Meta:
        # list_serializer_class = FilterReviewListSerializer
        model = Review
        fields = (
            'author',
            # 'email',
            # 'email1',
            'date',
            'text',
            'rate',
            # 'product',
            # 'children_review',
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
    Вывод изображений продукта
    """

    class Meta:
        model = CategoryImages
        # fields = "__all__"
        fields = (
            'src',
            'alt',
        )


class ProfileImageSerializer(serializers.ModelSerializer):
    """
    Вывод изображений аватара
    """

    class Meta:
        model = ProductImages
        # fields = "__all__"
        fields = (
            'src',
            'alt',
        )

    # def create(self, validated_data):
    #     return AvatarsImages.objects.create(**validated_data)
    #
    # def update(self, instance, validated_data):
    #     instance.src = validated_data.get("src", instance.src)
    #     instance.alt = validated_data.get("alt", instance.alt)
    #     instance.save()
    #     return instance


class TagSerializer(serializers.ModelSerializer):
    """
    Вывод тегов продукта
    """

    class Meta:
        model = Tag
        # fields = "__all__"
        fields = (
            # 'id',
            'name',
        )


class CategorySerializer(serializers.ModelSerializer):
    """
    Вывод категорий продукта
    """
    subcategories = RecursiveSerializer(many=True)
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
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    rating = serializers.FloatField()
    # date = serializers.DateTimeField(format=formats.get_format('DATETIME_FORMAT'))
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


# class ProductPopularSerializer(serializers.ModelSerializer):
#     images = ProductImageSerializer(many=True, read_only=True)
#     tags = TagSerializer(many=True, read_only=True)
#     reviews = serializers.SerializerMethodField()
#
#     class Meta:
#         model = ProductInstance
#         fields = (
#             'id',
#             'category',
#             'price',
#             'count',
#             'date',
#             'title',
#             'description',
#             'freeDelivery',
#             'images',
#             'tags',
#             'reviews',
#             'rating'
#         )
#
#     def get_reviews(self, instance):
#         return instance.get_review().count()

class ProductSalesSerializer(serializers.ModelSerializer):
    """
    Список продуктов для распродажи
    """
    images = ProductImageSerializer(many=True)
    id = serializers.SlugField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    salePrice = serializers.DecimalField(max_digits=10, decimal_places=2)

    dateFrom = serializers.SerializerMethodField()
    dateTo = serializers.SerializerMethodField()

    class Meta:
        model = ProductInstance
        fields = (
            'id',
            'price',
            'salePrice',
            # 'count',
            'dateFrom',
            'dateTo',
            'title',
            'images',
        )

    def get_dateFrom(self, obj):
        return obj.dateFrom.strftime("%m-%d")

    def get_dateTo(self, obj):
        return obj.dateTo.strftime("%m-%d")

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


# class ProductLimitedSerializer(serializers.ModelSerializer):
#     reviews_count = serializers.IntegerField()
#
#     class Meta:
#         model = ProductInstance
#         fields = (
#             'id',
#             # 'title',
#             # 'item_number',
#             'freeDelivery',
#             'price',
#             'count',
#             'available',
#             'archived',
#             'category',
#             # 'reviews',
#             'reviews_count',
#             'date',
#         )


class ProductDetailSerializer(serializers.ModelSerializer):
    # category = serializers.SlugRelatedField(slug_field='title', read_only=True)
    # tags = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    tags = TagSerializer(many=True)
    # tags2 = serializers.CharField(source='description')
    reviews = ReviewSerializer(many=True)
    images = ProductImageSerializer(many=True)
    specifications = PropertyInstanceProductSerializer(many=True)
    rating = serializers.FloatField()
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
            # 'tags2',
            # 'available',
            # 'archived',
            'reviews',
            # 'reviews2',
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


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#
#     class Meta:
#         model = Profile
#         # fields = "__all__"
#         fields = (
#             'fullName',
#             'email',
#             'phone',
#             # 'avatar',
#         )
#
#     def save(self):
#         profile = Profile(fullName=self.validated_data['fullName'], phone=self.validated_data['phone'])
#         profile.save()
#         return profile


# class ProfileSerializer(serializers.ModelSerializer):
#     """
#     Профиль ИИ, 1
#     """
#     class Meta:
#         model = Profile
#         fields = '__all__'
#         extra_kwargs = {'slug': {'read_only': True}}

# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email', read_only=True)
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'avatar', 'phone', 'email')
#
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         return {k: v for k, v in representation.items() if v is not None}


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     avatar = serializers.PrimaryKeyRelatedField(queryset=AvatarsImages.objects.all(), allow_null=True)
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#
#     def create(self, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         email = validated_data.pop('user').get('email')
#         user, created = User.objects.get_or_create(email=email)
#         profile = Profile.objects.create(user=user, **validated_data)
#         if avatar_data:
#             profile.avatar = avatar_data
#             profile.save()
#         return profile


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     avatar = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#
#     def get_avatar(self, obj):
#         avatar_instance = obj.avatar
#         if avatar_instance:
#             serializer = ProfileImageSerializer(avatar_instance)
#             return serializer.data
#         return None


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     # avatar = serializers.PrimaryKeyRelatedField(queryset=AvatarsImages.objects.all(), allow_null=True)
#     avatar = ProfileImageSerializer()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#
#     def create(self, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         email = validated_data.pop('user').get('email')
#         user, created = User.objects.get_or_create(email=email)
#         profile = Profile.objects.create(user=user, **validated_data)
#         if avatar_data:
#             profile.avatar = avatar_data
#             profile.save()
#         return profile
#
#     def update(self, instance, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         for key, value in validated_data.items():
#             setattr(instance, key, value)
#         if avatar_data:
#             instance.avatar = avatar_data
#         instance.save()
#         return instance


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     avatar = ProfileImageSerializer()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')

# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     avatar = ProfileImageSerializer()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#
#     def create(self, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         email = validated_data.pop('user').get('email')
#
#         user, created = User.objects.get_or_create(email=email)
#         profile = Profile.objects.create(user=user, **validated_data)
#
#         if avatar_data:
#             avatar = AvatarsImages.objects.create(**avatar_data)
#             profile.avatar = avatar
#             profile.save()
#
#         return profile


# class ProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email')
#     avatar = ProfileImageSerializer()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#
#     def create(self, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         email = validated_data.pop('user').get('email')
#         user, created = User.objects.get_or_create(email=email)
#         profile = Profile.objects.create(user=user, **validated_data)
#
#         if avatar_data:
#             profile.avatar = avatar_data
#             profile.save()
#
#         return profile
#
#     def update(self, instance, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#
#         for key, value in validated_data.items():
#             setattr(instance, key, value)
#
#         if avatar_data:
#             if instance.avatar:
#                 instance.avatar.src = avatar_data.get('src', instance.avatar.src)
#                 instance.avatar.alt = avatar_data.get('alt', instance.avatar.alt)
#                 instance.avatar.save()
#             else:
#                 avatar = AvatarsImages.objects.create(**avatar_data)
#                 instance.avatar = avatar
#
#         instance.save()
#         return instance


# class ProfileSerializer(serializers.ModelSerializer):
#     # email = serializers.EmailField(source='user.email')
#     email = serializers.EmailField(source='user.email', allow_null=True, allow_blank=True) #email не обновляется, но фронтом отображается
#     # email = serializers.EmailField(allow_null=True, allow_blank=True) #email обновляется, но фронтом не отображается
#     avatar = ProfileImageSerializer()
#
#     class Meta:
#         model = Profile
#         fields = ('fullName', 'email', 'phone', 'avatar')
#         # fields = ('fullName', 'phone', 'avatar')
#
#     def create(self, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         # email = validated_data.pop('user').get('email')
#         email = validated_data.get('user.email')
#         # user, created = User.objects.get_or_create(email=email)
#         user, created = User.objects.get_or_create(email=email)
#         profile = Profile.objects.create(user=user, **validated_data)
#         # if avatar_data:
#         #     profile.avatar = avatar_data
#         #     profile.save()
#         if avatar_data:
#             avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
#             profile.avatar = avatar
#             profile.save()
#         return profile
#
#     def update(self, instance, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#         # avatar_data = validated_data.get('avatar', None)
#         # email = validated_data.get('user', {}).get('email')
#         email = validated_data.get('user.email')
#         # email = validated_data.get('email')
#         print('----****--avatar_data--', avatar_data)
#         print('----****--validated_data--', validated_data)
#         print('----****--email--', email)
#         # if email:
#         if email is not None and email != instance.user.email:
#             instance.user.email = email
#             instance.user.save()
#
#         for key, value in validated_data.items():
#             setattr(instance, key, value)
#         if avatar_data:
#             avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
#             instance.avatar = avatar
#         instance.save()
#         return instance

class ProfileSerializer(serializers.ModelSerializer):
    """
    ИИ 4, email обновляется, но фронтом не отображается и аватар нужно обязятельно при обновлении загружать
    """
    email = serializers.EmailField(source='user.email', allow_null=True, allow_blank=True) #email не обновляется, но фронтом отображается
    # email = serializers.EmailField(allow_null=True, allow_blank=True) #email обновляется, но фронтом не отображается
    avatar = ProfileImageSerializer(required=False)

    class Meta:
        model = Profile
        fields = ('fullName', 'email', 'phone', 'avatar')

    def create(self, validated_data):
        avatar_data = validated_data.pop('avatar',)
        email = validated_data.get('user.email')

        user, created = User.objects.get_or_create(email=email)
        profile = Profile.objects.create(user=user, **validated_data)

        if avatar_data:
            avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
            profile.avatar = avatar
            profile.save()

        return profile

    def update(self, instance, validated_data):
        avatar_data = validated_data.pop('avatar', None)
        email = validated_data.get('email')

        if email is not None and email != instance.user.email:
            instance.user.email = email
            instance.user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if avatar_data is not None:
            avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
            instance.avatar = avatar

        instance.save()
        return instance

class SignUpSerializer(serializers.Serializer):
    """
    Регистрация ии 2, работает в рест, не работает во фронте, возможно 'name' это не 'fullName'
    """
    name = serializers.CharField(source='fullName', max_length=50)
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)

    class Meta:
        model = Profile
        fields = ['name', 'username', 'password']


# class SignUpSerializer(serializers.ModelSerializer):
#     """
#     Регистрация, работает 1
#     """
#     name = serializers.CharField(source='first_name')
#
#     class Meta:
#         model = User
#         fields = ['name', 'username', 'password']


# class SignInSerializer(serializers.ModelSerializer):
#     # name = serializers.CharField(source='first_name')
#
#     class Meta:
#         model = User
#         fields = ['username', 'password']


# class SignInSerializer(serializers.Serializer):
#     """
#         работает 1
#     """
#     username = serializers.CharField(
#         label="Username",
#         write_only=True
#     )
#     password = serializers.CharField(
#         label="Password",
#         # This will be used when the DRF browsable API is enabled
#         style={'input_type': 'password'},
#         trim_whitespace=False,
#         write_only=True
#     )
#
#     def validate(self, attrs):
#         # Take username and password from request
#         username = attrs.get('username')
#         password = attrs.get('password')
#
#         if username and password:
#             # Try to authenticate the user using Django auth framework.
#             user = authenticate(request=self.context.get('request'),
#                                 username=username, password=password)
#             if not user:
#                 # If we don't have a regular user, raise a ValidationError
#                 msg = 'Access denied: wrong username or password.'
#                 raise serializers.ValidationError(msg, code='authorization')
#         else:
#             msg = 'Both "username" and "password" are required.'
#             raise serializers.ValidationError(msg, code='authorization')
#         # We have a valid user, put it in the serializer's validated_data.
#         # It will be used in the view.
#         attrs['user'] = user
#         return attrs


class LoginSerializer(serializers.Serializer):
    """
    ии
    """
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)


# class ProfileAvatarSerializer(serializers.ModelSerializer):
#     avatar = ProfileImageSerializer(required=False)
#
#     class Meta:
#         model = Profile
#         fields = ('avatar',)
#
#     def update(self, instance, validated_data):
#         avatar_data = validated_data.pop('avatar', None)
#
#         if avatar_data is not None:
#             avatar, created = AvatarsImages.objects.get_or_create(**avatar_data)
#             instance.avatar = avatar
#
#         instance.save()
#         return instance

class ProfileAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.PrimaryKeyRelatedField(
        queryset=AvatarsImages.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Profile
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        instance.avatar = avatar
        instance.save()
        return instance