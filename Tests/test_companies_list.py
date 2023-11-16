"""API-тесты для эндпойнта /api/companies/"""

from collections import Counter
from random import randint
from typing import Union

import allure
import pytest
import requests
from allure_commons.types import Severity
from pytest_check import check

# Элементы проекта
from Data import json_schemas
from Helpers.api_client import APIClient
from Helpers.helpers import Helpers
from base_tests import BaseStatusHeadersSchemaTests


@pytest.mark.smoke
@allure.parent_suite("/api/companies")
@allure.suite("Запрос без дополнительных параметров и хедеров")
class TestCompaniesWithoutParams:
    """Проверяет ответ на запрос по BASE_URL без дополнительных параметров и хедеров"""

    @allure.title("Статус-код, хедеры, схема при запросе на /api/companies без параметров")
    @allure.severity(Severity.BLOCKER)
    def test_companies_base_status_headers_schema(self, response_get_base_url):
        """Проверяет базовые параметры ответа: статус-код, хедеры, соответствие json-схеме"""
        tester = BaseStatusHeadersSchemaTests(response_get_base_url, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

    @allure.title("Лимит выдачи по умолчанию (3) при запросе на /api/companies без параметров")
    @allure.severity(Severity.NORMAL)
    def test_companies_default_limit(
            self, response_get_base_url):
        """Проверяет лимит по умолчанию (равен 3)"""
        body = response_get_base_url.json()
        body_length = len(body['data'])
        assert body_length == 3, f"Тело ответа содержит {body_length} объектов вместо 3"


@pytest.mark.regression
@allure.parent_suite("/api/companies")
@allure.suite("Запрос по протоколу HTTP")
@allure.severity(Severity.NORMAL)
class TestCompaniesRedirectFromHTTP:
    """Проверяет ответ на запрос по протоколу http вместо https"""

    @allure.title("Статус-код по HTTP")
    def test_companies_status_code_with_http(
            self, response_with_http: Union[requests.Response]):
        """Проверяет, что код ответа соответствует перенаправлению"""
        assert response_with_http.status_code == 301, \
            f": Код ответа: {response_with_http.status_code}, должен быть: 301"

    @allure.title("Протокол ответа при запросе по HTTP")
    def test_companies_response_proto_with_http(
            self, response_with_http: Union[requests.Response]):
        """Проверяет, что ответ получен по протоколу http"""
        proto = response_with_http.url.split(':')[0]
        assert proto == 'http', f"Протокол ответа: {proto}, должен быть: http"

    @allure.title("Хедеры при запросе по HTTP")
    def test_companies_response_headers_with_http(
            self, response_with_http: Union[requests.Response]):
        """Проверяет значения хедеров Connection и Location при запросе через http"""
        check.is_in(response_with_http.headers['Location'],
                    ('https://send-request.me/api/companies',
                     'https://send-request.me/api/companies/'),
                    f"Перенаправление на неверный адрес: {response_with_http.headers['Location']}")
        check.equal(response_with_http.headers['Connection'], 'keep-alive',
                    "Значение хедера Connection не keep-alive")


@allure.parent_suite("/api/companies")
@allure.suite("Запрос с фильтром по статусу компании")
class TestCompaniesWithStatus:
    """Проверяет результат запроса с параметром 'Статус компании'"""

    # Чтение из файла реализовано исключительно для практики, в данном случае необходимости в нем нет
    @pytest.mark.smoke
    @pytest.mark.parametrize('status, expected',
                             Helpers.get_test_data_from_csv('company_statuses.csv'))
    @allure.title("Запрос на /api/companies с фильтром по валидному статусу ({status})")
    @allure.severity(Severity.CRITICAL)
    def test_companies_filtered_by_valid_status(self, status: str, expected: str,
                                                api_client: APIClient, total_status_counter: Union[Counter]):
        """
        Проверяет соответствие ответа запросу с ВАЛИДНЫМ параметром 'Статус компании' и лимитом,
        равным общему числу компаний в базе: статус всех компаний в ответе и их количество.
        Проверяет базовые параметры ответа: статус-код, хедеры, соответствие json-схеме
        """
        response = api_client.get(path=f"/?status={status}&limit=7")  # Известно, что в базе всего 7 компаний
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        data = body['data']
        check.is_true(all([item['company_status'] == expected for item in data]),
                      f"Current: {[item['company_status'] for item in data]}, {expected}")
        check.equal(len(data), total_status_counter[status],
                    f"Количество компаний в ответе ({len(data)}) не соответствует "
                    f"ожидаемому ({total_status_counter[status]})")

    @pytest.mark.negative
    @pytest.mark.regression
    @pytest.mark.parametrize('invalid_status', ['ABC', 123])
    @allure.title("Запрос на /api/companies с фильтром по невалидному статусу ({invalid_status})")
    @allure.severity(Severity.MINOR)
    def test_companies_filtered_by_invalid_status(self, invalid_status: Union[str, int], api_client: APIClient):
        """Проверяет ответ на запрос с НЕВАЛИДНЫМ параметром 'Статус компании'"""
        response = api_client.get(path=f"/?status={invalid_status}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.regression
@allure.parent_suite("/api/companies")
@allure.suite("Запрос на /api/companies с указанием лимита выдачи результатов")
# TODO: запрос на /api/companies с указанием СТАТУСА компании и лимита выдачи результатов (параметризация)
class TestCompaniesWithLimit:
    """
    Проверяет результат запроса с параметром 'Лимит'.
    Известно, что в базе всего 7 объектов
    """

    @pytest.mark.parametrize('limit', [randint(0, 6), 7, randint(8, 100)])
    @allure.title("Валидный лимит ({limit}) при запросе на /api/companies")
    @allure.severity(Severity.NORMAL)
    def test_companies_with_valid_limit(self, limit: int, api_client: APIClient):
        """Проверяет результат запроса с ВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client.get(path=f"/?limit={limit}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        if limit <= 7:
            assert body_length == limit, f"В теле ответа {body_length} объекта(-ов) вместо {limit}"
        else:
            assert body_length == 7, f"В теле ответа {body_length} объекта(-ов) вместо 7"

    # Вероятный БАГ: при параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_limit', ['ABC', -1])
    @allure.title("Невалидный лимит ({invalid_limit}) при запросе на /api/companies")
    @allure.severity(Severity.MINOR)
    def test_companies_with_invalid_limit(self, invalid_limit, api_client: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client.get(path=f"/?limit={invalid_limit}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.regression
@allure.parent_suite("/api/companies")
@allure.suite("Запрос с указанием оффсета для выдачи результатов")
class TestCompaniesWithOffset:
    """
    Проверяет результат запроса с параметром 'Оффсет'.
    Известно, что в базе всего 7 объектов
    """

    @allure.title("Валидный оффсет, не превышающий число объектов в базе, при запросе на /api/companies")
    @allure.severity(Severity.MINOR)
    def test_companies_with_valid_offset_within_range(self, api_client: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'Оффсет', НЕ ПРЕВЫШАЮЩИМ
        фактическое число объектов в базе (7)
        """
        offset = randint(0, 6)
        response = api_client.get(path=f"/?offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        first_id = body['data'][0]['company_id']
        assert first_id == offset + 1, f"В теле ответа список сдвинут на {first_id - 1} единиц вместо {offset}"

    @allure.title("Валидный оффсет, превышающий число объектов в базе, при запросе на /api/companies")
    @allure.severity(Severity.MINOR)
    def test_companies_with_valid_offset_out_of_range(self, api_client: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'Оффсет', ПРЕВЫШАЮЩИМ
        фактическое число объектов в базе (7)
        """
        offset = randint(7, 30)
        response = api_client.get(path=f"/?offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        assert body_length == 0, f"Сдвиг списка на {offset} единиц не применен"

    # Вероятный БАГ: при параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_offset', ['ABC', -1])
    @allure.title("Невалидный оффсет ({invalid_offset}) при запросе на /api/companies")
    @allure.severity(Severity.MINOR)
    def test_companies_with_invalid_offset(self, invalid_offset: Union[str, int], api_client: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ параметром 'Оффсет'"""
        response = api_client.get(path=f"/?offset={invalid_offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.regression
@allure.parent_suite("/api/companies")
@allure.suite("Запрос с указанием лимита и оффсета для выдачи результатов")
@allure.severity(Severity.MINOR)
class TestCompaniesWithLimitAndOffset:
    """Проверяет результат запроса с заданными одновременно параметрами 'Оффсет' и 'Лимит'"""

    @allure.title("Валидный лимит и оффсет при запросе на /api/companies")
    def test_companies_with_valid_limit_and_offset(self, api_client: APIClient):
        """Проверяет результат запроса с заданными одновременно ВАЛИДНЫМИ параметрами 'Оффсет' и 'Лимит'"""
        # TODO: добавить тесты на невалидные сочетания
        limit = randint(1, 7)
        offset = randint(0, 6)
        response = api_client.get(path=f"/?limit={limit}&offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANIES_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        first_id = body['data'][0]['company_id']
        amount_to_be = min(7 - offset, limit)
        assert body_length == amount_to_be and first_id == offset + 1, \
            f"В теле ответа должно быть {amount_to_be} объектов, сейчас {body_length} объекта(-ов). " \
            f"Список должен быть сдвинут на {offset} единиц, сейчас на {first_id - 1} единиц. "
