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
    """Фильтр комментариев комментариев, (parents)"""

    def to_representation(self, data):
        data = data.filter(parent=None)
        return super().to_representation(data)


class RecursiveSerializer(serializers.Serializer):
    """Для рекурсивного вывода children, если понадобится"""

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
    # email = UserSerializer(many=True)
    # email = serializers.EmailField(source='email')
    email = serializers.SerializerMethodField()

    def get_email(self, obj):
        return obj.author.email

    class Meta:
        # list_serializer_class = FilterReviewListSerializer
        model = Review
        fields = (
            'author',
            'email',
            'date',
            'text',
            'rate',
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
    Вывод изображений категории
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
            'reviews',
            'specifications',
            'rating',
        )


class ProfileSerializer(serializers.ModelSerializer):
    """
    Профиль, email обновляется, но фронтом не отображается и аватар нужно обязятельно при обновлении загружать
    """
    email = serializers.EmailField(
        source='user.email',
        allow_null=True,
        allow_blank=True
    )  # email не обновляется, но фронтом отображается
    # email = serializers.EmailField(allow_null=True, allow_blank=True) #email обновляется, но фронтом не отображается
    avatar = ProfileImageSerializer(required=False)

    class Meta:
        model = Profile
        fields = (
            'fullName',
            'email',
            'phone',
            'avatar'
        )

    def create(self, validated_data):
        avatar_data = validated_data.pop('avatar', )
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
    Регистрация, работает в рест, не работает во фронте, возможно 'name' это не 'fullName'
    """
    name = serializers.CharField(source='fullName', max_length=50)
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)

    class Meta:
        model = Profile
        fields = ['name', 'username', 'password']


# class SignUpSerializer(serializers.ModelSerializer):
#     """
#     Регистрация, работает
#     """
#     name = serializers.CharField(source='first_name')
#
#     class Meta:
#         model = User
#         fields = ['name', 'username', 'password']


# class SignInSerializer(serializers.Serializer):
#     """
#     Вход, работает
#     """
#     username = serializers.CharField(
#         label="Username",
#         write_only=True
#     )
#     password = serializers.CharField(
#         label="Password",
#         style={'input_type': 'password'},
#         trim_whitespace=False,
#         write_only=True
#     )
#
#     def validate(self, attrs):
#         username = attrs.get('username')
#         password = attrs.get('password')
#
#         if username and password:
#             user = authenticate(request=self.context.get('request'),
#                                 username=username, password=password)
#             if not user:
#                 msg = 'Access denied: wrong username or password.'
#                 raise serializers.ValidationError(msg, code='authorization')
#         else:
#             msg = 'Both "username" and "password" are required.'
#             raise serializers.ValidationError(msg, code='authorization')
#         attrs['user'] = user
#         return attrs


class LoginSerializer(serializers.Serializer):
    """
    Вход
    """
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)


class ProfileAvatarSerializer(serializers.ModelSerializer):
    """
    Аватар
    """
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


# class BasketItemSerializer(serializers.ModelSerializer):
#     """
#     Корзина
#     """
#     # product = ProductListSerializer()
#     # product = serializers.IntegerField(read_only=True)  # Для POST-запроса по id, не работает
#     product = serializers.IntegerField()  # Для POST-запроса по product, работает, но не на фронте
#     # id = serializers.IntegerField(source='product.id')  # Поле id указывает на атрибут id продукта, не работает
#     count = serializers.IntegerField()
#
#     class Meta:
#         model = BasketItem
#         fields = (
#             # 'id',
#             'product',
#             'count',
#         )


class BasketItemSerializer(serializers.ModelSerializer):
    """
    Продукт и его количество из корзины
    """
    product = serializers.PrimaryKeyRelatedField(queryset=ProductInstance.objects.all())
    count = serializers.IntegerField()

    class Meta:
        model = BasketItem
        fields = (
            'id',
            'product',
            'count',
        )


# class BasketProductSerializer(serializers.ModelSerializer):
#     """
#     Данные продукта из корзины
#     """
#     tags = TagSerializer(many=True, read_only=True)
#     images = ProductImageSerializer(many=True, read_only=True)
#     reviews = serializers.IntegerField(source='reviews_count', read_only=True)
#     rating = serializers.FloatField()
#     date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')
#     count = serializers.IntegerField()
#     # items = BasketItemSerializer(many=True, read_only=True)
#     items = BasketItemSerializer(many=True, read_only=True, source='product_basketitem')
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
#             'rating',
#             'items'
#         )
#
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#
#         basket_items = BasketItem.objects.filter(product=instance)
#         first_item = basket_items.first()
#         if first_item:
#             count = first_item.count
#             representation['count'] = count
#
#         return representation


class BasketProductSerializer(serializers.ModelSerializer):
    """
    Данные продукта из корзины
    """
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count', read_only=True)
    rating = serializers.FloatField()
    date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')
    count = serializers.IntegerField()
    items = BasketItemSerializer(many=True, read_only=True)

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
            'items'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        basket_items = BasketItem.objects.filter(product=instance)
        first_item = basket_items.first()
        if first_item:
            count = first_item.count
            representation['count'] = count

        return representation


class BasketSerializer(serializers.ModelSerializer):
    """
    Чья корзина
    """
    items = BasketItemSerializer(many=True, read_only=True)
    # items = BasketItemSerializer(many=True, read_only=True, source='items')
    # items = BasketProductSerializer(many=True, read_only=True)

    class Meta:
        model = Basket
        # fields = '__all__'
        fields = (
            'id',
            'items'
        )


class DeleteBasketItemSerializer(serializers.Serializer):
    """
    Для удаления корзины
    """
    id = serializers.IntegerField()
    count = serializers.IntegerField()


class OrderBasketProductSerializer(serializers.ModelSerializer):
    """
    Данные продукта из заказа
    """
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count', read_only=True)
    rating = serializers.FloatField()
    date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')
    count = serializers.IntegerField()
    items = BasketItemSerializer(many=True, read_only=True)

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
            'items',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Добавляем поле reviews в representation
        reviews = ProductInstance.objects.filter(available=True, id=instance.id).annotate(
            reviews_count=Count('reviews')).values('reviews_count').first()
        if reviews:
            representation['reviews'] = reviews['reviews_count']
        else:
            representation['reviews'] = 0
        # Добавляем поле count в representation
        basket_items = BasketItem.objects.filter(product=instance)
        first_item = basket_items.first()
        if first_item:
            count = first_item.count
            representation['count'] = count
        return representation


class OrderBasketItemSerializer(serializers.ModelSerializer):
    """
    Продукт и его количество из заказа
    """
    product = serializers.SerializerMethodField()

    def get_product(self, obj):
        return OrderBasketProductSerializer(obj.product).data

    class Meta:
        model = BasketItem
        # fields = '__all__'
        fields = ('product',)


class OrderBasketSerializer(serializers.ModelSerializer):
    """
    Чья корзина из заказа
    """
    items = serializers.SerializerMethodField()

    def get_items(self, obj):
        products = obj.products.all()
        product_data = []
        for product in products:
            product_serialized = OrderBasketProductSerializer(product).data
            product_data.append(product_serialized)
        return product_data

    class Meta:
        model = Basket
        fields = (
            'items',
        )


class OrderSerializer(serializers.ModelSerializer):  # наверно нужно будет убрать поле profile из модели (есть user)
    """
    Заказ
    """
    fullName = serializers.CharField(source='profile.fullName')
    email = serializers.EmailField(source='profile.user.email')
    phone = serializers.CharField(source='profile.phone')

    # fullName = serializers.CharField(source='basket.user.profile.fullName')
    # email = serializers.EmailField(source='basket.user.email')
    # phone = serializers.CharField(source='basket.user..phone')

    createdAt = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)', required=False)
    products = serializers.SerializerMethodField()
    totalCost = serializers.SerializerMethodField()

    deliveryType = serializers.CharField(source='get_deliveryType_display')
    paymentType = serializers.CharField(source='get_paymentType_display')
    status = serializers.CharField(source='get_status_display')

    def get_products(self, obj):
        products = obj.basket.products.all()  # Обращаюсь к атрибуту "products" через связь с объектом "Basket"
        product_data = []
        for product in products:
            product_serialized = OrderBasketProductSerializer(product).data
            product_data.append(product_serialized)
        return product_data

    def get_totalCost(self, obj):
        return obj.calculate_total_cost()

    def create(self, validated_data):
        basket_data = validated_data.pop('basket')
        order = Order.objects.create(**validated_data)
        basket = Basket.objects.create(order=order, **basket_data)
        basket.calculate_total_cost()  # Рассчитываем и сохраняем суммарную стоимость продуктов в корзине
        return order

    class Meta:
        model = Order
        fields = (
            'id',
            'createdAt',
            'fullName',
            'email',
            'phone',
            'deliveryType',
            'paymentType',
            'totalCost',
            'status',
            'city',
            'address',
            'products',
        )


class PaymentCardSerializer(serializers.ModelSerializer):
    """
    Оплата (карта)
    """
    class Meta:
        model = PaymentCard
        exclude = ['id', 'owner']
        # fields = '__all__'
