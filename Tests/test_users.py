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
        # Поскольку пользователей можно удалять, проверить точный оффсет по первому ID нельзя, однако
        #  благодаря тому, что список в теле ответа сохраняет сортировку, следует проверить, что первый ID
        #  в ответе не меньше оффсета в запросе
        assert first_id >= offset + 1, f"В теле ответа список сдвинут менее чем на {offset} единиц: " \
                                       f"первый ID {first_id}"

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
        # Поскольку пользователей можно удалять, проверить точный оффсет по первому ID нельзя, однако
        #  благодаря тому, что список в теле ответа сохраняет сортировку, следует проверить, что первый ID
        #  в ответе не меньше оффсета в запросе
        assert body_length == limit and first_id >= offset + 1, \
            f"В теле ответа должно быть {limit} объектов, сейчас {body_length} объекта(-ов). " \
            f"Список сдвинут менее чем на {offset} единиц: первый ID {first_id}"


# endregion Общее для эндпойнтов

# region Специфика эндпойнта
@allure.parent_suite("/api/users")
@allure.suite("POST-запрос для создания пользователя")
@allure.severity(Severity.CRITICAL)
class TestCreateUser:
    """Создает пользователя"""

    @staticmethod
    def _create_body_object(last_name=None, first_name=None, company_id=None):
        """Формирует тело для POST-запроса"""
        body = {}
        if last_name is not None:
            body["last_name"] = last_name
        if first_name is not None:
            body["first_name"] = first_name
        if company_id is not None:
            body["company_id"] = company_id

        return json.dumps(body)

    @pytest.mark.smoke
    @allure.title("Создание пользователя в существующей активной компании со всеми валидно заполненными полями")
    def test_create_user_with_full_valid_data(self, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя со всеми валидно заполненными полями и указанием существующей активной компании"""
        company_id = choice(companies_grouped_by_statuses['ACTIVE'])
        first_name, last_name, company_id = "Corneliy", "Shnabs", company_id
        request_body = self._create_body_object(first_name=first_name, last_name=last_name, company_id=company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        response_body = response.json()

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()

        # Удаление пользователя. Фикстуру finalizer не использую, потому что нужно передавать id пользователя.
        # Создавать пользователя (и получать id) прямо в фикстуре не вариант, потому что в данном случае это суть теста.
        user_id = response_body["user_id"]
        api_client_users.delete(path=f"/{user_id}")

        assert (response_body["first_name"] == first_name and
                response_body["last_name"] == last_name and
                response_body["company_id"] == company_id), \
            f"Тело ответа не соответствует запросу. Получен ответ {response.json()}"

    @pytest.mark.smoke
    @allure.title("Создание пользователя с валидно заполненным только обязательным полем")
    def test_create_user_with_only_required_valid_data(self, api_client_users: APIClient):
        """Создает пользователя с валидно заполненным обязательным полем last_name"""
        last_name = "Shnabs"
        request_body = self._create_body_object(last_name)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        response_body = response.json()

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()

        # Удаление пользователя. Фикстуру finalizer не использую, потому что нужно передавать id пользователя.
        # Создавать пользователя (и получать id) прямо в фикстуре не вариант, потому что в данном случае это суть теста.
        user_id = response_body["user_id"]
        api_client_users.delete(path=f"/{user_id}")

        response_body = response.json()
        assert response_body["last_name"] == last_name, \
            f"Тело ответа не соответствует запросу. Получен ответ {response.json()}"

    # БАГ в документации: поле 'last_name' должно принимать только string, а фактически бэк преобразует в string
    # числа и bool
    @pytest.mark.smoke
    @pytest.mark.parametrize('last_name', [0, 0.5, -1, False, True])
    @allure.title("Создание пользователя с нетекстовым, но непустым значением в обязательном поле")
    def test_create_user_with_nums_and_bool_in_required_data(self, last_name, api_client_users: APIClient):
        """Создает пользователя с нетекстовым, но непустым значением в обязательном поле last_name"""
        request_body = self._create_body_object(last_name)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        response_body = response.json()

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()

        # Удаление пользователя. Фикстуру finalizer не использую, потому что нужно передавать id пользователя.
        # Создавать пользователя (и получать id) прямо в фикстуре не вариант, потому что в данном случае это суть теста.
        user_id = response_body["user_id"]
        api_client_users.delete(path=f"/{user_id}")

        response_body = response.json()
        assert response_body["last_name"] == str(last_name), \
            f"Тело ответа не соответствует запросу. Получен ответ {response.json()}"

    @pytest.mark.smoke
    @pytest.mark.negative
    @allure.title("Создание пользователя с пустым телом запроса, в т.ч. без обязательного поля")
    def test_create_user_without_data(self, api_client_users: APIClient):
        """Создает пользователя с пустым телом запроса, в т.ч. без обязательного поля"""
        request_body = self._create_body_object()
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    @pytest.mark.smoke
    @pytest.mark.negative
    @allure.title("Создание пользователя с непустым телом запроса, но без обязательного поля")
    def test_create_user_without_required_data(self, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя с непустым телом запроса, но без обязательного поля"""
        company_id = choice(companies_grouped_by_statuses['ACTIVE'])
        request_body = self._create_body_object(first_name="Corneliy", company_id=company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    # Вероятный БАГ: бэк позволяет успешно создать пользователя с пустой строкой в обязательном поле
    @pytest.mark.smoke
    @pytest.mark.negative
    @pytest.mark.parametrize('last_name', [None, '', ' '])
    @allure.title("Создание пользователя с пустым значением в обязательном поле")
    def test_create_user_with_empty_required_data(self, last_name, api_client_users: APIClient):
        """Создает пользователя с пустым значением в обязательном поле last_name"""
        request_body = self._create_body_object(last_name=last_name)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    @pytest.mark.smoke
    @pytest.mark.parametrize('last_name', [[], {1: True}, (3,)])
    @allure.title("Создание пользователя с невалидным значением в обязательном поле")
    def test_create_user_with_invalid_required_data(self, last_name, api_client_users: APIClient):
        """Создает пользователя с нетекстовым, но непустым значением в обязательном поле last_name"""
        request_body = self._create_body_object(last_name)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    # TODO: create_user с разными статусами компаний, с несуществующей компанией, с невалидными данными
    #  в необязательных полях, с длинным текстом в полях, с company_id != integer

# endregion Специфика эндпойнта
