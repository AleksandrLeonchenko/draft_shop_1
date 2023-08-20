from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


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


def get_client_ip(request):
    """
    Функция, которая определяет IP-адрес юзера
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
