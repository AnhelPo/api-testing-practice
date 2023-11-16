"""Базовые тесты для всех запросов"""

import requests
from jsonschema import Draft4Validator, ValidationError
from pytest_check import check


class BaseStatusHeadersSchemaTests:
    """
    Базовые тесты для всех запросов: проверка кода ответа, общих хедеров,
    соответствия тела ответа JSON-схеме
    """

    def __init__(self, response: requests.Response, schema: dict, code: int):
        self.response = response
        self.schema_to_be = schema
        self.code_to_be = code

    def _test_status_code(self):
        """Проверяет соответствие кода ответа ожидаемому"""
        assert self.response.status_code == self.code_to_be, \
            f"Код ответа: {self.response.status_code}, должен быть: {self.code_to_be}"

    def _test_headers(self):
        """Проверяет значения хедеров Content-Type и Connection"""
        check.equal(self.response.headers["Content-Type"], "application/json",
                    "Значение хедера Content-Type не application/json")
        check.equal(self.response.headers["Connection"], "keep-alive",
                    "Значение хедера Connection не keep-alive")

    def _test_match_with_json_schema(self):
        """Проверяет соответствие тела ответа JSON-схеме"""
        try:
            Draft4Validator(self.schema_to_be).validate(self.response.json())
        except ValidationError:
            raise AssertionError(
                f'Тело ответа не соответствует JSON-схеме, {self.response.json()}')

    def test_status_headers_schema(self):
        """
        Проверяет код ответа, значения хедеров Content-Type и Connection
        и соответствие тела ответа JSON-схеме
        """
        self._test_status_code()
        self._test_headers()
        self._test_match_with_json_schema()
