from typing import List, Dict, Any
from rest_framework import serializers
from . import models
from .models import User, BasketItem, Basket, Order, PaymentCard
from app_products.models import ProductInstance
from app_products.serializers import TagSerializer, ProductImageSerializer
# from typing import Type


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

    def to_representation(self, instance: ProductInstance) -> Dict[str, Any]:
        """
        Если пользователь передан в контекст, ищем объект корзины для этого пользователя
        и подсчитываем общее количество данного продукта в корзине.
        Затем это общее количество добавляем в представление продукта в поле count:
        """
        representation: Dict[str, Any] = super().to_representation(instance)  # Получаем базовое представление продукта

        user = self.context.get('user')  # Получаем пользователя из контекста
        if user:
            basket = Basket.objects.get(user=user)  # Получаем корзину пользователя
            basket_items = BasketItem.objects.filter(product=instance, basket=basket)  # Получаем продукты в корзине
            # Получаем общее количества продукта в корзине с использованием. Если количество не определено, то 0.
            total_count = basket_items.aggregate(total_count=models.Sum('count'))['total_count'] or 0
            representation['count'] = total_count  # Добавляем количество данного продукта в корзине

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
    createdAt = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    deliveryType = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_deliveryType(self, obj) -> str:
        delivery_type = obj.get_deliveryType_display()  # Получаем отображаемое значение поля "deliveryType"
        return delivery_type

    def get_paymentType(self, obj) -> str:
        payment_type = obj.get_paymentType_display()
        return payment_type

    def get_status(self, obj) -> str:
        status = obj.get_status_display()
        return status

    def get_totalCost(self, obj) -> float:
        return obj.calculate_total_cost()

    def get_products(self, obj) -> List[Dict[str, Any]]:

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

    def get_deliveryType(self, obj) -> str:
        delivery_type = obj.get_deliveryType_display()  # Получаем отображаемое значение поля "deliveryType"
        return delivery_type

    def get_paymentType(self, obj) -> str:
        payment_type = obj.get_paymentType_display()
        return payment_type

    def get_status(self, obj) -> str:
        status = obj.get_status_display()
        return status

    def get_products(self, obj) -> List[Dict[str, Any]]:

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

    def get_totalCost(self, obj) -> float:
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
