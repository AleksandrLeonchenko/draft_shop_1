from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
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

