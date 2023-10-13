from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import json
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from typing import List, Union, Any, Dict

class CustomPaginationProducts(PageNumberPagination):
    page_size: int = 2
    page_query_param: str = 'currentPage'
    max_page_size: int = 20

    def get_paginated_response(self, data: List[Dict[str, Any]]) -> Response:
        return Response({
            'items': data,
            'currentPage': self.page.number,
            'lastPage': self.page.paginator.count,
        })


class PaginationProducts(PageNumberPagination):
    page_size: int = 2
    max_page_size: int = 1000

    def get_paginated_response(self, data: List[Dict[str, Any]]) -> Response:
        return Response({
            'items': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data
        })


class PlainListJSONParser(JSONParser):
    """
    Анализирует входные данные, сериализованные в формате JSON, в список примитивов Python.
    Это позволяет в POST-запросе отправлять данные в формате массива.
    """

    media_type: str = 'application/json'

    def parse(self, stream: Any, media_type: Union[None, str] = None,
              parser_context: Union[None, Dict[str, Any]] = None) -> List[Any]:
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', 'utf-8')

        try:
            data = stream.read().decode(encoding)
            return json.loads(data)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))
