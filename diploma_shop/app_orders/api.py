import json
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
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = (AllowAny,)
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        basket = get_object_or_404(Basket, user=request.user)
        basket_items = basket.items2.all()
        product_ids = basket_items.values_list('product_id', flat=True)

        # Используем новый метод менеджера
        products = ProductInstance.objects.filter_and_annotate(product_ids)
        serializer = BasketProductSerializer(products, many=True, context={'user': request.user})
        return Response(serializer.data)

    def post(self, request):
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket, created = Basket.objects.get_or_create(user=request.user)  # Измененная строка
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']
            product = ProductInstance.objects.get(id=product_id)

            # Пытаемся получить существующий элемент корзины для данного продукта
            try:
                basket_item = BasketItem.objects.get(basket=basket, product=product)
                # Если существует, обновляем его количество
                basket_item.count += count
                basket_item.save()
            except BasketItem.DoesNotExist:
                # Если не существует, создаем новый элемент корзины
                basket_item = BasketItem.objects.create(basket=basket, product=product, count=count)
                basket_item.save()

            basket_items = basket.items2.all()
            product_ids = basket_items.values_list('product_id', flat=True)
            products = ProductInstance.objects.filter_and_annotate(product_ids)
            serializer = BasketProductSerializer(products, many=True, context={'user': request.user})

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
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
    parser_classes = [PlainListJSONParser]
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request, *args, **kwargs):
        # orders = Order.objects.all()
        orders = Order.objects.filter(id=request.user.basket2.order.id)
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)

    @transaction.atomic  # использование транзакции для обеспечения целостности данных
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            basket = Basket.objects.get(user=user)  # получаем корзину пользователя
        except Basket.DoesNotExist:
            return Response({'error': 'User does not have a basket'}, status=status.HTTP_400_BAD_REQUEST)

        # Если у пользователя уже есть корзина, просто создаем заказ и привязываем к этой корзине
        order = Order.objects.create(basket=basket)

        # Возвращаем ответ с идентификатором созданного заказа
        return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer

    # Маппинг строковых значений на числовые
    delivery_type_mapping = {
        'Доставка': 1,
        'Экспресс-доставка': 2,
    }
    payment_type_mapping = {
        'Онлайн картой': 1,
        'Онлайн со случайного чужого счёта': 2,
    }
    status_mapping = {
        'ожидание платежа': 1,
        'оплачено': 2,
    }

    def post(self, request, *args, **kwargs):  # работает как в сваггере
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

        # return Response(OrderDetailSerializer(order).data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_200_OK)


class PaymentCardAPIView(generics.CreateAPIView):
    """
    Оплата (карта оплаты)
    """
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    serializer_class = PaymentCardSerializer

    def create(self, request, *args, **kwargs):

        try:
            # Пытаемся прочитать данные как JSON
            data = json.loads(list(request.POST.keys())[0])
        except (json.JSONDecodeError, IndexError):
            # Если это не удается, принимаем данные как обычные форменные данные
            data = request.POST.dict()
            data.pop('csrfmiddlewaretoken', None)  # Удалите csrfmiddlewaretoken

        serializer = self.get_serializer(data=data)
        # serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        number = serializer.validated_data.get('number')
        if int(number) % 2 != 0 or len(str(number)) > 8:
            return Response({'error': 'Invalid card number'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(owner=request.user)

        return Response(status=status.HTTP_200_OK)
        # return Response(serializer.data, status=status.HTTP_200_OK)