"""API-тесты для эндпойнта /api/users. Work in progress"""

import json
from random import randint, choice
from typing import Union

import allure
import pytest
import requests
from allure_commons.types import Severity
from pytest_check import check

# Элементы проекта
from Data import json_schemas
from Helpers.api_client import APIClient
from base_tests import BaseStatusHeadersSchemaTests


# region Общее для эндпойнтов
@allure.parent_suite("/api/users")
@allure.suite("Базовый запрос списка пользователей")
class TestUsersWithoutParams:
    """Проверяет ответ на запрос к эндпойнту /api/users"""

    @allure.title("Статус-код, хедеры, схема при запросе на /api/users без параметров")
    @allure.severity(Severity.BLOCKER)
    def test_users_list_base_status_headers_schema(self, response_get_base_users: Union[requests.Response]):
        """Проверяет базовые параметры ответа: статус-код, хедеры, соответствие json-схеме"""
        tester = BaseStatusHeadersSchemaTests(response_get_base_users, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

    @allure.title("Лимит выдачи по умолчанию (3) при запросе на /api/users без параметров")
    @allure.severity(Severity.NORMAL)
    def test_users_default_limit(self, response_get_base_users: Union[requests.Response]):
        """Проверяет лимит по умолчанию (равен 3)"""
        body = response_get_base_users.json()
        body_length = len(body['data'])
        assert body_length == 3, f"Тело ответа содержит {body_length} объектов вместо 3"


@pytest.mark.regression
@allure.parent_suite("/api/users")
@allure.suite("Запрос по протоколу HTTP")
@allure.severity(Severity.NORMAL)
class TestUsersRedirectFromHTTP:
    """Проверяет ответ на запрос по протоколу http вместо https"""

    @allure.title("Статус-код по HTTP")
    def test_users_status_code_with_http(self, response_users_with_http: Union[requests.Response]):
        """Проверяет, что код ответа соответствует перенаправлению"""
        assert response_users_with_http.status_code == 301, \
            f": Код ответа: {response_users_with_http.status_code}, должен быть: 301"

    @allure.title("Протокол ответа при запросе по HTTP")
    def test_users_response_proto_with_http(self, response_users_with_http: Union[requests.Response]):
        """Проверяет, что ответ получен по протоколу http"""
        proto = response_users_with_http.url.split(':')[0]
        assert proto == 'http', f"Протокол ответа: {proto}, должен быть: http"

    @allure.title("Хедеры при запросе по HTTP")
    def test_users_response_headers_with_http(self, response_users_with_http: Union[requests.Response]):
        """Проверяет значения хедеров Connection и Location при запросе через http"""
        check.is_in(response_users_with_http.headers['Location'],
                    ('https://send-request.me/api/users',
                     'https://send-request.me/api/users/'),
                    f"Перенаправление на неверный адрес: {response_users_with_http.headers['Location']}")
        check.equal(response_users_with_http.headers['Connection'], 'keep-alive',
                    "Значение хедера Connection не keep-alive")


@pytest.mark.regression
@allure.parent_suite("/api/users")
@allure.suite("Запрос на /api/users с указанием лимита выдачи результатов")
class TestUsersWithLimit:
    """Проверяет результат запроса с параметром 'Лимит'"""

    @pytest.mark.parametrize('limit', [0, randint(1, 100)])
    @allure.title("Валидный лимит ({limit}) при запросе на /api/users")
    @allure.severity(Severity.NORMAL)
    def test_users_with_valid_limit(self, limit: int, api_client_users: APIClient):
        """Проверяет результат запроса с ВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client_users.get(path=f"/?limit={limit}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        assert body_length == limit, f"В теле ответа {body_length} объекта(-ов) вместо {limit}"

    # Вероятный БАГ: при параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_limit', ['ABC', -1])
    @allure.title("Невалидный лимит ({invalid_limit}) при запросе на /api/users")
    @allure.severity(Severity.MINOR)
    def test_users_with_invalid_limit(self, invalid_limit, api_client_users: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client_users.get(path=f"/?limit={invalid_limit}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.regression
@allure.parent_suite("/api/users")
@allure.suite("Запрос с указанием оффсета для выдачи результатов")
class TestUsersWithOffset:
    """
    Проверяет результат запроса с параметром 'Оффсет'.
    Известно, что в базе всего 7 объектов
    """

    @allure.title("Валидный оффсет, не превышающий число объектов в базе, при запросе на /api/users")
    @allure.severity(Severity.NORMAL)
    def test_users_with_valid_offset_within_range(self, api_client_users: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'Оффсет', НЕ ПРЕВЫШАЮЩИМ
        фактическое число объектов в базе
        """
        offset = randint(0, 50)
        response = api_client_users.get(path=f"/?offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        first_id = body['data'][0]['user_id']
        assert first_id == offset + 1, f"В теле ответа список сдвинут на {first_id - 1} единиц вместо {offset}"

    @allure.title("Валидный оффсет, превышающий число объектов в базе, при запросе на /api/users")
    @allure.severity(Severity.NORMAL)
    def test_users_with_valid_offset_out_of_range(self, api_client_users: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'Оффсет', ПРЕВЫШАЮЩИМ
        фактическое число объектов в базе
        """
        offset = randint(100000, 100100)
        response = api_client_users.get(path=f"/?offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        assert body_length == 0, f"Сдвиг списка на {offset} единиц не применен"

    # Вероятный БАГ: при параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_offset', ['ABC', -1])
    @allure.title("Невалидный оффсет ({invalid_offset}) при запросе на /api/users")
    @allure.severity(Severity.MINOR)
    def test_users_with_invalid_offset(self, invalid_offset: Union[str, int], api_client_users: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ параметром 'Оффсет'"""
        response = api_client_users.get(path=f"/?offset={invalid_offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.regression
@allure.parent_suite("/api/users")
@allure.suite("Запрос с указанием лимита и оффсета для выдачи результатов")
@allure.severity(Severity.MINOR)
class TestUsersWithLimitAndOffset:
    """Проверяет результат запроса с заданными одновременно параметрами 'Оффсет' и 'Лимит'"""

    @allure.title("Валидный лимит и оффсет при запросе на /api/users")
    def test_users_with_valid_limit_and_offset(self, api_client_users: APIClient):
        """Проверяет результат запроса с заданными одновременно ВАЛИДНЫМИ параметрами 'Оффсет' и 'Лимит'"""
        # TODO: добавить тесты на невалидные сочетания
        limit = randint(1, 100)
        offset = randint(0, 100)
        response = api_client_users.get(path=f"/?limit={limit}&offset={offset}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        first_id = body['data'][0]['user_id']
        assert body_length == limit and first_id == offset + 1, \
            f"В теле ответа должно быть {limit} объектов, сейчас {body_length} объекта(-ов). " \
            f"Список должен быть сдвинут на {offset} единиц, сейчас на {first_id - 1} единиц. "


# endregion Общее для эндпойнтов

# region Специфика эндпойнта
class TestCreateUser:
    """Создает пользователя"""

    @staticmethod
    def _create_body_object(first_name, last_name, company_id):
        """Формирует тело для POST-запроса"""
        return json.dumps(
            {"first_name": first_name,
             "last_name": last_name,
             "company_id": company_id})

    def test_create_user_with_valid_data(self, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя со всеми валидно заполненными полями и указанием существующей активной компании"""
        company_id = choice(companies_grouped_by_statuses['ACTIVE'])
        first_name, last_name, company_id = "Corneliy", "Shnabs", company_id
        request_body = self._create_body_object(first_name, last_name, company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()

        response_body = response.json()
        assert (response_body["first_name"] == first_name and
                response_body["last_name"] == last_name and
                response_body["company_id"] == company_id), \
            f"Тело ответа не соответствует запросу. Получен ответ {response.json()}"

# endregion Специфика эндпойнта
