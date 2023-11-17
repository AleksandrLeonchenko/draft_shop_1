import json
from typing import Any, List, Dict, Union
from django.db.models import QuerySet
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from .models import Basket, BasketItem, Order
from .serializers import BasketProductSerializer, BasketItemSerializer, OrderSerializer, OrderDetailSerializer, \
    PaymentCardSerializer
from .service import PlainListJSONParser
from app_products.models import ProductInstance


class BasketView(APIView):
    """
    Корзина
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]

    def get(self, request: Any) -> Response:
        basket = get_object_or_404(Basket, user=request.user)  # Получаем корзину текущего пользователя
        basket_items = basket.items2.all()  # Получаем все элементы корзины
        product_ids = basket_items.values_list('product_id', flat=True)  # Получаем ID всех продуктов в корзине
        products = ProductInstance.objects.filter_and_annotate(product_ids)  # Получаем продукты и их аннотации
        serializer = BasketProductSerializer(products, many=True, context={'user': request.user})  # Сериализация данных
        return Response(serializer.data)

    def post(self, request: Any) -> Response:
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket, created = Basket.objects.get_or_create(
                user=request.user)  # Получаем или создаем корзину пользователя
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']
            product = ProductInstance.objects.get(id=product_id)  # Получаем конкретный продукт

            try:
                basket_item = BasketItem.objects.get(basket=basket, product=product)  # Ищем продукт в корзине
                basket_item.count += count  # Обновляем количество
                # basket_item.save()
            except BasketItem.DoesNotExist:  # Если продукта нет в корзине
                basket_item = BasketItem.objects.create(basket=basket, product=product,
                                                        count=count)  # Создаем новый элемент корзины
                # basket_item.save()

            basket_item.save()
            basket_items = basket.items2.all()
            product_ids = basket_items.values_list('product_id', flat=True)
            products = ProductInstance.objects.filter_and_annotate(product_ids)
            serializer = BasketProductSerializer(products, many=True, context={'user': request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Any) -> Response:
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket = Basket.objects.get(user=request.user)
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']

            try:
                basket_item = BasketItem.objects.get(basket=basket, product_id=product_id)
            except BasketItem.DoesNotExist:
                return Response({"error": "Product not found in basket"}, status=status.HTTP_404_NOT_FOUND)

            if basket_item.count == count:
                basket_item.delete()
            elif basket_item.count > count:
                basket_item.count -= count
                basket_item.save()
            else:
                return Response({"error": "The basket contains fewer items than you're trying to remove"},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Item(s) removed successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIView(APIView):
    """
    Заказы
    """
    parser_classes: List[Any] = [PlainListJSONParser]
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        orders = Order.objects.filter(id=request.user.basket2.order.id)
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)

    @transaction.atomic  # использование транзакции для обеспечения целостности данных
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        user = request.user

        try:
            basket = Basket.objects.get(user=user)  # получаем корзину пользователя
        except Basket.DoesNotExist:
            return Response({'error': 'User does not have a basket'}, status=status.HTTP_400_BAD_REQUEST)

        # Если у пользователя уже есть корзина, просто создаем заказ и привязываем к этой корзине
        order = Order.objects.create(basket=basket)
        return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(RetrieveAPIView):
    """
    Заказ
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]
    queryset: QuerySet = Order.objects.all()
    serializer_class: Any = OrderDetailSerializer

    # Маппинг строковых значений на числовые
    delivery_type_mapping: Dict[str, int] = {
        'Доставка': 1,
        'Экспресс-доставка': 2,
    }
    payment_type_mapping: Dict[str, int] = {
        'Онлайн картой': 1,
        'Онлайн со случайного чужого счёта': 2,
    }
    status_mapping: Dict[str, int] = {
        'ожидание платежа': 1,
        'оплачено': 2,
    }

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        try:
            order = self.get_object()  # получение объекта заказа по id
        except Http404:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data  # данные, полученные из тела POST-запроса

        if 'fullName' in data:
            order.basket.user.profile2.fullName = data['fullName']
        if 'email' in data:
            order.basket.user.email = data['email']
        if 'phone' in data:
            order.basket.user.profile2.phone = data['phone']
        if 'deliveryType' in data:
            order.deliveryType = self.delivery_type_mapping.get(data['deliveryType'], order.deliveryType)
        if 'paymentType' in data:
            order.paymentType = self.payment_type_mapping.get(data['paymentType'], order.paymentType)
        if 'totalCost' in data:
            order.totalCost = data['totalCost']
        if 'status' in data:
            order.status = self.status_mapping.get(data['status'], order.status)
        if 'city' in data:
            order.city = data['city']
        if 'address' in data:
            order.address = data['address']

        # Сохранение изменений
        order.save()
        order.basket.user.profile2.save()
        order.basket.user.save()

        return Response(status=status.HTTP_200_OK)


class PaymentCardAPIView(generics.CreateAPIView):
    """
    Оплата (карта оплаты)
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]
    serializer_class: Any = PaymentCardSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:

        try:
            # Пытаемся прочитать данные как JSON
            data = json.loads(list(request.POST.keys())[0])
        except (json.JSONDecodeError, IndexError):
            # Если это не удается, принимаем данные как обычные форменные данные
            data = request.POST.dict()
            data.pop('csrfmiddlewaretoken', None)  # Удаляем csrfmiddlewaretoken

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        number = serializer.validated_data.get('number')
        if int(number) % 2 != 0 or len(str(number)) > 8:
            return Response({'error': 'Invalid card number'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(owner=request.user)

        return Response(status=status.HTTP_200_OK)
