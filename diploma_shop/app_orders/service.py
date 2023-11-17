import json
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from typing import List, Union, Any, Dict


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
