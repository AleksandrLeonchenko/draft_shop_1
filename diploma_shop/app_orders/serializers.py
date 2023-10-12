# from django.db.models import Count
# from django.utils import formats
# from rest_framework import serializers, request, exceptions
from rest_framework import serializers
# from django.shortcuts import get_object_or_404
# from rest_framework.serializers import raise_errors_on_nested_writes
# from rest_framework.utils import model_meta
# from django.contrib.auth import authenticate
# from datetime import datetime

from . import models
from .models import User, BasketItem, Basket, Order, PaymentCard
from app_products.models import ProductInstance
from app_products.serializers import TagSerializer, ProductImageSerializer


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User
    """

    class Meta:
        model = User
        fields = ('email',)


class BasketItemSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()
    id = serializers.IntegerField()

    class Meta:
        model = BasketItem
        fields = (
            'id',
            'count'
        )


class BasketProductSerializer(serializers.ModelSerializer):
    """
    Данные продукта из корзины
    """
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(source='images2', many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count', read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)
    date = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)')
    # date = serializers.DateTimeField(format='YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]')
    count = serializers.IntegerField(default=0)

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

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        user = self.context.get('user')
        if user:
            basket = Basket.objects.get(user=user)
            basket_items = BasketItem.objects.filter(product=instance, basket=basket)
            total_count = basket_items.aggregate(total_count=models.Sum('count'))['total_count'] or 0
            representation['count'] = total_count

        return representation


class BasketSerializer(serializers.ModelSerializer):
    """
    Чья корзина
    """
    items = BasketItemSerializer(many=True, read_only=True)

    class Meta:
        model = Basket
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


class OrderSerializer(serializers.ModelSerializer):
    """
    Заказ
    """
    fullName = serializers.CharField(source='basket.user.profile.fullName', read_only=True)
    email = serializers.EmailField(source='basket.user.email', read_only=True)
    phone = serializers.CharField(source='basket.user.profile.phone', read_only=True)
    products = serializers.SerializerMethodField(source='products2')
    totalCost = serializers.SerializerMethodField()
    # createdAt = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)', read_only=True)
    createdAt = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    deliveryType = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_deliveryType(self, obj):
        delivery_type = obj.get_deliveryType_display()  # Получаем отображаемое значение поля "deliveryType"
        return delivery_type

    def get_paymentType(self, obj):
        payment_type = obj.get_paymentType_display()
        return payment_type

    def get_status(self, obj):
        status = obj.get_status_display()
        return status

    def get_totalCost(self, obj):
        return obj.calculate_total_cost()

    def get_products(self, obj):

        products = obj.basket.products.all()  # Получаем все продукты в этом заказе
        product_ids = [product.id for product in products]  # Получаем их ID
        annotated_products = ProductInstance.objects.filter_and_annotate(product_ids)  # Аннотируем их
        annotated_products_dict = {
            product.id: {'reviews': product.reviews_count, 'rating': product.average_rating}
            for product in annotated_products
        }
        product_data = []
        # Создаем словарь, чтобы проверять, добавлен ли уже продукт в список
        added_products = {}
        for product in products:
            # Если продукт уже добавлен, пропускаем его
            if product.id in added_products:
                continue
            product_serialized = BasketProductSerializer(product).data  # Сериализуем каждый продукт
            product_serialized.update(annotated_products_dict.get(product.id, {'reviews': 0, 'rating': 0}))
            product_data.append(product_serialized)
            added_products[product.id] = True  # Отмечаем, что продукт добавлен

        return product_data



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


class OrderDetailSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source='basket.user.profile.fullName', read_only=True)
    email = serializers.EmailField(source='basket.user.email', read_only=True)
    phone = serializers.CharField(source='basket.user.profile.phone', read_only=True)
    products = serializers.SerializerMethodField()
    totalCost = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(format='%a %b %d %Y %H:%M:%S GMT%z (%Z)', read_only=True)
    deliveryType = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_deliveryType(self, obj):
        delivery_type = obj.get_deliveryType_display()  # Получаем отображаемое значение поля "deliveryType"
        return delivery_type

    def get_paymentType(self, obj):
        payment_type = obj.get_paymentType_display()
        return payment_type

    def get_status(self, obj):
        status = obj.get_status_display()
        return status



    def get_products(self, obj):

        products = obj.basket.products.all()  # Получаем все продукты в этом заказе
        product_ids = [product.id for product in products]  # Получаем их ID
        # print('///---product_ids---///', product_ids)
        annotated_products = ProductInstance.objects.filter_and_annotate(product_ids)  # Аннотируем их
        annotated_products_dict = {
            product.id: {'reviews': product.reviews_count, 'rating': product.average_rating}
            for product in annotated_products
        }
        product_data = []
        # Создаем словарь, чтобы проверять, добавлен ли уже продукт в список
        added_products = {}
        for product in products:
            # Если продукт уже добавлен, пропускаем его
            if product.id in added_products:
                continue
            product_serialized = BasketProductSerializer(product).data  # Сериализуем каждый продукт
            product_serialized.update(annotated_products_dict.get(product.id, {'reviews': 0, 'rating': 0}))
            product_data.append(product_serialized)
            added_products[product.id] = True  # Отмечаем, что продукт добавлен

        return product_data

    def get_totalCost(self, obj):
        return obj.calculate_total_cost()

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
