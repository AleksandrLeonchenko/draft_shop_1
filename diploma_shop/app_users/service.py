from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import json
# from rest_framework import parsers
# from django_filters import rest_framework as product_filters
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError

# from .models import *


class CustomPaginationProducts(PageNumberPagination):
    page_size = 2
    page_query_param = 'currentPage'
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'currentPage': self.page.number,
            'lastPage': self.page.paginator.count,
        })


class PaginationProducts(PageNumberPagination):
    page_size = 2
    max_page_size = 1000

    def get_paginated_response(self, data):
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

    media_type = 'application/json'

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', 'utf-8')

        try:
            data = stream.read().decode(encoding)
            return json.loads(data)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % str(exc))

