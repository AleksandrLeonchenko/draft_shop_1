from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import json
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from typing import List, Union, Any, Dict

class CustomPaginationProducts(PageNumberPagination):
    page_size: int = 2  # Определение базового размера страницы
    page_query_param: str = 'currentPage'  # Параметр запроса для указания текущей страницы
    max_page_size: int = 20  # Определение максимального размера страницы

    def get_paginated_response(self, data: List[Dict[str, Any]]) -> Response:
        return Response({
            'items': data,  # Возвращает текущие элементы страницы
            'currentPage': self.page.number,  # Возвращает номер текущей страницы
            'lastPage': self.page.paginator.count,  # Возвращает общее количество элементов
        })


class PaginationProducts(PageNumberPagination):
    page_size: int = 2  # Определение базового размера страницы
    max_page_size: int = 1000  # Определение максимального размера страницы

    def get_paginated_response(self, data: List[Dict[str, Any]]) -> Response:
        return Response({
            'items': {
                'next': self.get_next_link(),  # Получение ссылки на следующую страницу
                'previous': self.get_previous_link()  # Получение ссылки на предыдущую страницу
            },
            'count': self.page.paginator.count,  # Возвращает общее количество элементов
            'results': data  # Возвращает текущие элементы страницы
        })


class PlainListJSONParser(JSONParser):
    """
    Анализирует входные данные, сериализованные в формате JSON, в список примитивов Python.
    Это позволяет в POST-запросе отправлять данные в формате массива.
    """

    media_type: str = 'application/json'  # Определение медиа-типа

    def parse(self, stream: Any, media_type: Union[None, str] = None,
              parser_context: Union[None, Dict[str, Any]] = None) -> List[Any]:
        parser_context = parser_context or {}  # Установка контекста анализатора
        encoding = parser_context.get('encoding',
                                      'utf-8')  # Получение кодировки из контекста или установка значения по умолчанию

        try:
            data = stream.read().decode(encoding)  # Чтение и декодирование данных
            return json.loads(data)  # Конвертация декодированных данных из JSON в Python список
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))  # Возбуждение исключения в случае ошибки анализа
