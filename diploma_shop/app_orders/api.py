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
    Управление содержимым корзины пользователя.

    Methods:
    - get: Получить содержимое корзины пользователя.
    - post: Добавить продукт в корзину.
    - delete: Удалить продукт(ы) из корзины.

    Permissions:
    - IsAuthenticated: Пользователь должен быть аутентифицирован.

    Authentication:
    - SessionAuthentication: Аутентификация по сессии.

    Returns:
    - 200 OK: Успешное получение, добавление или удаление данных корзины.
    - 204 No Content: Успешное удаление элементов корзины.
    - 400 Bad Request: Ошибка в запросе или данных.
    - 404 Not Found: Не найден продукт в корзине.
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]

    def get(self, request: Any) -> Response:
        """
        Получить содержимое корзины пользователя.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 200 OK: Успешное получение содержимого корзины.
        """
        basket = get_object_or_404(Basket, user=request.user)  # Получаем корзину текущего пользователя
        basket_items = basket.items2.all()  # Получаем все элементы корзины
        product_ids = basket_items.values_list('product_id', flat=True)  # Получаем ID всех продуктов в корзине
        products = ProductInstance.objects.filter_and_annotate(product_ids)  # Получаем продукты и их аннотации
        serializer = BasketProductSerializer(products, many=True, context={'user': request.user})  # Сериализация данных
        return Response(serializer.data)

    def post(self, request: Any) -> Response:
        """
        Добавить продукт в корзину.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 200 OK: Успешное добавление продукта в корзину.
        - 400 Bad Request: Ошибка в запросе или данных.
        """
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket, created = Basket.objects.get_or_create(
                user=request.user)  # Получаем или создаем корзину пользователя, сделавшего запрос
            product_id = serializer.validated_data['id']
            count = serializer.validated_data['count']
            product = ProductInstance.objects.get(id=product_id)  # Получаем конкретный продукт по его id

            try:
                basket_item = BasketItem.objects.get(basket=basket, product=product)  # Ищем продукт в корзине
                basket_item.count += count  # Обновляем количество
                # basket_item.save()
            except BasketItem.DoesNotExist:  # Если продукта нет в корзине
                basket_item = BasketItem.objects.create(basket=basket, product=product,
                                                        count=count)  # Создаем новый элемент корзины
                # basket_item.save()

            basket_item.save()  # Сохранение изменений
            basket_items = basket.items2.all()  # Получаем все элементы корзины пользователя
            product_ids = basket_items.values_list('product_id', flat=True)  # Идентификаторы всех продуктов в корзине
            products = ProductInstance.objects.filter_and_annotate(product_ids)  # Экземпляры продуктов с аннотациями
            serializer = BasketProductSerializer(products, many=True, context={'user': request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Any) -> Response:
        """
        Удалить продукт(ы) из корзины.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 204 No Content: Успешное удаление продукта(ов) из корзины.
        - 400 Bad Request: Ошибка в запросе или данных.
        - 404 Not Found: Не найден продукт в корзине.
        """
        serializer = BasketItemSerializer(data=request.data)
        if serializer.is_valid():
            basket = Basket.objects.get(user=request.user)  # Корзина пользователя
            product_id = serializer.validated_data['id']  # Идентификатор продукта и количества из валидированных данных
            count = serializer.validated_data['count']  # Количество продукта из валидированных данных

            try:
                # Поиск элемента корзины для удаляемого продукта:
                basket_item = BasketItem.objects.get(basket=basket, product_id=product_id)
            except BasketItem.DoesNotExist:
                # Если продукт не найден в корзине, возврат 404
                return Response({"error": "Product not found in basket"}, status=status.HTTP_404_NOT_FOUND)

            if basket_item.count == count:
                # Удаление продукта из корзины, если количество совпадает
                basket_item.delete()
            elif basket_item.count > count:
                # Уменьшение количества продукта в корзине, если требуемое количество меньше, чем имеющееся
                basket_item.count -= count
                basket_item.save()
            else:
                # Возврат 400, если требуемое количество больше, чем имеющееся в корзине
                return Response({"error": "The basket contains fewer items than you're trying to remove"},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Item(s) removed successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIView(APIView):
    """
    Управление заказами пользователя.

    Methods:
    - get: Получить заказы пользователя.
    - post: Создать новый заказ пользователя.

    Parser Classes:
    - PlainListJSONParser: Используемый парсер данных.

    Permissions:
    - IsAuthenticated: Пользователь должен быть аутентифицирован.

    Authentication:
    - SessionAuthentication: Аутентификация по сессии.

    Returns:
    - 200 OK: Успешное получение заказов пользователя.
    - 201 Created: Успешное создание нового заказа.
    - 400 Bad Request: Ошибка в запросе или данных.
    """
    parser_classes: List[Any] = [PlainListJSONParser]  # Определение используемых парсеров данных
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Получить заказы пользователя.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 200 OK: Успешное получение заказов пользователя.
        """
        # Получение всех заказов пользователя, привязанных к его корзине
        orders = Order.objects.filter(id=request.user.basket2.order.id)
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)

    @transaction.atomic
    # использование транзакции в методе "post" гарантирует, что создание заказа и
    # привязка его к корзине будут выполнены как атомарная операция
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Создать новый заказ пользователя.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 201 Created: Успешное создание нового заказа.
        - 400 Bad Request: Ошибка в запросе или данных.
        """
        user = request.user

        try:
            basket = Basket.objects.get(user=user)  # получаем корзину пользователя
        except Basket.DoesNotExist:
            # Возвращение 400, если у пользователя отсутствует корзина
            return Response({'error': 'User does not have a basket'}, status=status.HTTP_400_BAD_REQUEST)

        # Если у пользователя уже есть корзина, просто создаем заказ и привязываем к этой корзине
        order = Order.objects.create(basket=basket)
        return Response({"orderId": order.id}, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(RetrieveAPIView):
    """
    Получение и обновление информации о заказе.

    Methods:
    - post: Обновление информации о заказе.

    Permissions:
    - IsAuthenticated: Пользователь должен быть аутентифицирован.

    Authentication:
    - SessionAuthentication: Аутентификация по сессии.

    Attributes:
    - queryset (QuerySet): Запрос для получения всех объектов заказов.
    - serializer_class: Сериализатор для заказов.

    Returns:
    - 200 OK: Успешное обновление информации о заказе.
    - 404 Not Found: Заказ не найден.
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]
    queryset: QuerySet = Order.objects.all()
    serializer_class: Any = OrderDetailSerializer

    # Маппинг строковых значений на числовые для типа доставки
    delivery_type_mapping: Dict[str, int] = {
        'Доставка': 1,
        'Экспресс-доставка': 2,
    }
    # Маппинг строковых значений на числовые для типа оплаты
    payment_type_mapping: Dict[str, int] = {
        'Онлайн картой': 1,
        'Онлайн со случайного чужого счёта': 2,
    }
    # Маппинг строковых значений на числовые для статуса заказа
    status_mapping: Dict[str, int] = {
        'ожидание платежа': 1,
        'оплачено': 2,
    }

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Обновление информации о заказе.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 200 OK: Успешное обновление информации о заказе.
        - 404 Not Found: Заказ не найден.
        """
        try:
            order = self.get_object()  # Получение объекта заказа по id
        except Http404:
            # Возвращение 404, если заказ не найден
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data  # Данные, полученные из тела POST-запроса

        # Обновление данных заказа, если они присутствуют в запросе
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
    Создание информации о платежной карте пользователя для оплаты.

    Methods:
    - create: Создание информации о платежной карте.

    Permissions:
    - IsAuthenticated: Пользователь должен быть аутентифицирован.

    Authentication:
    - SessionAuthentication: Аутентификация по сессии.

    Attributes:
    - serializer_class: Сериализатор для платежной карты.

    Returns:
    - 200 OK: Успешное создание информации о платежной карте.
    - 400 Bad Request: Некорректные данные или неверный формат номера карты.
    """
    permission_classes: List[Any] = [permissions.IsAuthenticated]
    authentication_classes: List[Any] = [SessionAuthentication]
    serializer_class: Any = PaymentCardSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Создание информации о платежной карте пользователя для оплаты.

        Parameters:
        - request (Request): Объект запроса.

        Returns:
        - 200 OK: Успешное создание информации о платежной карте.
        - 400 Bad Request: Некорректные данные или неверный формат номера карты.
        """
        try:
            # Пытаемся прочитать данные как JSON
            data = json.loads(list(request.POST.keys())[0])
        except (json.JSONDecodeError, IndexError):
            # Если это не удается, принимаем данные как обычные форменные данные
            data = request.POST.dict()
            data.pop('csrfmiddlewaretoken', None)  # Удаляем csrfmiddlewaretoken

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():  # Если данные не прошли валидацию сериализатора, то 400:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        number = serializer.validated_data.get('number')  # Получение номера карты
        # Проверка на корректность номера карты (четное число, не более 8 цифр):
        if int(number) % 2 != 0 or len(str(number)) > 8:
            return Response({'error': 'Invalid card number'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(owner=request.user)  # Сохранение данных карты, привязанных к пользователю

        return Response(status=status.HTTP_200_OK)
