"""API-тесты для эндпойнта /api/users. Work in progress"""

import json
from random import randint, choice
from typing import Union, Any

import allure
import pytest
import requests
from allure_commons.types import Severity
from faker import Faker
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
@allure.suite("Запрос по протоколу HTTP на /api/users")
@allure.severity(Severity.NORMAL)
class TestUsersRedirectFromHTTP:
    """Проверяет ответ на запрос по протоколу http вместо https"""

    @allure.title("Статус-код при запросе по HTTP на /api/users")
    def test_users_status_code_with_http(self, response_users_with_http: Union[requests.Response]):
        """Проверяет, что код ответа соответствует перенаправлению"""
        assert response_users_with_http.status_code == 301, \
            f": Код ответа: {response_users_with_http.status_code}, должен быть: 301"

    @allure.title("Протокол ответа при запросе по HTTP на /api/users")
    def test_users_response_proto_with_http(self, response_users_with_http: Union[requests.Response]):
        """Проверяет, что ответ получен по протоколу http"""
        proto = response_users_with_http.url.split(':')[0]
        assert proto == 'http', f"Протокол ответа: {proto}, должен быть: http"

    @allure.title("Хедеры при запросе по HTTP на /api/users")
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

    @pytest.mark.parametrize('limit',
                             [0, randint(1, 100)])
    @allure.title("Валидный лимит ({limit}) при запросе на /api/users")
    @allure.severity(Severity.NORMAL)
    def test_users_with_valid_limit(self, limit: int, api_client_users: APIClient):
        """Проверяет результат запроса с ВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client_users.get(params={'limit': limit})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        assert body_length == limit, f"В теле ответа {body_length} объекта(-ов) вместо {limit}"

    # Вероятный БАГ: при явно невалидном параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_limit',
                             ['ABC', -1])
    @allure.title("Невалидный лимит ({invalid_limit}) при запросе на /api/users")
    @allure.severity(Severity.MINOR)
    def test_users_with_invalid_limit(self, invalid_limit: Union[str, int], api_client_users: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ значением параметра 'Лимит'"""
        response = api_client_users.get(params={'limit': invalid_limit})
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
        response = api_client_users.get(params={'offset': offset})
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
        response = api_client_users.get(params={'offset': offset})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USERS_MAIN, 200)
        tester.test_status_headers_schema()

        body = response.json()
        body_length = len(body['data'])
        assert body_length == 0, f"Сдвиг списка на {offset} единиц не применен"

    # Вероятный БАГ: при параметре -1 возвращается 200 вместо 422. В документации не описано
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_offset',
                             ['ABC', -1])
    @allure.title("Невалидный оффсет ({invalid_offset}) при запросе на /api/users")
    @allure.severity(Severity.MINOR)
    def test_users_with_invalid_offset(self, invalid_offset: Union[str, int], api_client_users: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ параметром 'Оффсет'"""
        response = api_client_users.get(params={'offset': invalid_offset})
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
        response = api_client_users.get(params={'limit': limit, 'offset': offset})
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

    fake = Faker()

    @staticmethod
    def _create_body_object(**kwargs):
        """Формирует тело для POST-запроса"""
        return json.dumps(kwargs)

    @pytest.mark.smoke
    @allure.title("Пользователь в существующей активной компании со всеми валидно заполненными полями создан")
    def test_create_user_with_full_valid_data(self, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя со всеми валидно заполненными полями и указанием существующей активной компании"""
        company_id = choice(companies_grouped_by_statuses['ACTIVE'])
        first_name, last_name, company_id = (
            TestCreateUser.fake.first_name(), TestCreateUser.fake.last_name(), company_id)
        request_body = self._create_body_object(first_name=first_name, last_name=last_name, company_id=company_id)

        # Проверяем ответ на запрос на создание пользователя
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()
        response_create_user_body = response.json()
        assert (response_create_user_body["first_name"] == first_name and
                response_create_user_body["last_name"] == last_name and
                response_create_user_body["company_id"] == company_id), \
            f"Тело ответа не соответствует запросу. Получен ответ {response_create_user_body}"

        # Проверяем ответ на запрос на получение созданного пользователя
        user_id = response_create_user_body["user_id"]
        response = api_client_users.get(path=f"/{user_id}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_BY_ID, 200)
        tester.test_status_headers_schema()
        response_get_user_body = response.json()
        assert (response_get_user_body["first_name"] == first_name and
                response_get_user_body["last_name"] == last_name and
                response_get_user_body["company_id"] == company_id and
                response_get_user_body["user_id"] == user_id), \
            f"Ответ на запрос по ID созданного пользователя {user_id} не соответствует данным, указанным при " \
            f"создании пользователя. Получен ответ {response_get_user_body}. " \
            f"Должно быть: {dict(**response_create_user_body, **{'user_id': user_id})}"

        # Удаление пользователя. Фикстуру finalizer не использую, потому что нужно передавать id пользователя.
        # Создавать пользователя (и получать id) прямо в фикстуре не вариант, потому что в данном случае это суть теста.
        api_client_users.delete(path=f"/{user_id}")

    @pytest.mark.smoke
    @allure.title("Пользователь с валидно заполненным только обязательным полем создан")
    def test_create_user_with_only_required_valid_data(self, api_client_users: APIClient):
        """Создает пользователя с валидно заполненным обязательным полем last_name"""
        last_name = TestCreateUser.fake.last_name()
        request_body = self._create_body_object(last_name=last_name)

        # Проверяем ответ на запрос на создание пользователя
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_CREATED, 201)
        tester.test_status_headers_schema()
        response_create_user_body = response.json()
        assert response_create_user_body["last_name"] == last_name, \
            f"Тело ответа не соответствует запросу. Получен ответ {response.json()}"

        # Проверяем ответ на запрос на получение созданного пользователя
        user_id = response_create_user_body["user_id"]
        response = api_client_users.get(path=f"/{user_id}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.USER_BY_ID, 200)
        tester.test_status_headers_schema()
        response_get_user_body = response.json()
        assert (response_get_user_body["last_name"] == last_name and
                response_get_user_body["user_id"] == user_id), \
            f"Ответ на запрос по ID созданного пользователя {user_id} не соответствует данным, указанным при " \
            f"создании пользователя. Получен ответ {response_get_user_body}. " \
            f"Должно быть: {dict(**response_create_user_body, **{'user_id': user_id})}"

        # Удаление пользователя. Фикстуру finalizer не использую, потому что нужно передавать id пользователя.
        # Создавать пользователя (и получать id) прямо в фикстуре не вариант, потому что в данном случае это суть теста.
        api_client_users.delete(path=f"/{user_id}")

    @pytest.mark.smoke
    @allure.title("Пользователь с пустым телом запроса, в т.ч. без обязательного поля, не создан")
    def test_create_user_without_data(self, api_client_users: APIClient):
        """Создает пользователя с пустым телом запроса, в т.ч. без обязательного поля"""
        request_body = self._create_body_object()
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    @pytest.mark.smoke
    @allure.title("Пользователь с непустым телом запроса, но без обязательного поля не создан")
    def test_create_user_without_required_data(self, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя с непустым телом запроса, но без обязательного поля"""
        company_id = choice(companies_grouped_by_statuses['ACTIVE'])
        request_body = self._create_body_object(first_name=TestCreateUser.fake.first_name(), company_id=company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    # Вероятный БАГ: бэк позволяет успешно создать пользователя с пустой строкой в обязательном поле
    @pytest.mark.smoke
    @pytest.mark.negative
    @pytest.mark.parametrize('last_name',
                             [None, '', ' '],
                             ids=['None', 'Empty string', 'String with space'])
    @allure.title("Пользователь с пустым значением в обязательном поле не создан")
    def test_create_user_with_empty_required_data(self, last_name: Union[None, str], api_client_users: APIClient):
        """Создает пользователя с пустым значением в обязательном поле last_name"""
        request_body = self._create_body_object(last_name=last_name)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    @pytest.mark.smoke
    @pytest.mark.parametrize('status',
                             ['CLOSED', 'BANKRUPT'])
    @allure.title("Пользователь со всеми валидно заполненными полями в закрытой компании не создан")
    def test_create_user_with_closed_company_id(
            self, status: str, api_client_users: APIClient, companies_grouped_by_statuses: dict):
        """Создает пользователя со всеми валидно заполненными полями в закрытой компании"""
        company_id = choice(companies_grouped_by_statuses[status])
        first_name, last_name, company_id = (
            TestCreateUser.fake.first_name(), TestCreateUser.fake.last_name(), company_id)
        request_body = self._create_body_object(first_name=first_name, last_name=last_name, company_id=company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.BAD_REQUEST_400, 400)
        tester.test_status_headers_schema()

    @pytest.mark.smoke
    @allure.title("Пользователь со всеми валидно заполненными полями в компании с несуществующим ID не создан")
    def test_create_user_with_nonexistent_company_id(self, api_client_users: APIClient):
        """Создает пользователя со всеми валидно заполненными полями в компании с несуществующим ID"""
        company_id = randint(8, 100)
        first_name, last_name, company_id = (
            TestCreateUser.fake.first_name(), TestCreateUser.fake.last_name(), company_id)
        request_body = self._create_body_object(first_name=first_name, last_name=last_name, company_id=company_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.NOT_FOUND_404, 404)
        tester.test_status_headers_schema()

    # БАГ: при float в company_id пользователь создается в компании с id = trunc(company_id)
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize('invalid_id',
                             ['ABC', '', ' ', 1.5],
                             ids=['String', 'Empty string', 'String with space', 'float'])
    @allure.severity(Severity.MINOR)
    @allure.title("Пользователь со всеми валидно заполненными полями в компании с невалидным ID не создан")
    def test_create_user_with_invalid_company_id(self, invalid_id: Union[str, float], api_client_users: APIClient):
        """Создает пользователя со всеми валидно заполненными полями в компании с невалидным ID"""
        request_body = self._create_body_object(
            first_name=TestCreateUser.fake.first_name(), last_name=TestCreateUser.fake.last_name(),
            company_id=invalid_id)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    # БАГ: поля 'last_name', 'first_name' должны принимать только string, а фактически бэк преобразует
    # в string числа и bool
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize('name',
                             ['last_name', 'first_name'])
    @pytest.mark.parametrize('value',
                             [0, 0.5, -1, False, True, [], {1: True}, (3,)],
                             ids=['int', 'float', 'negative_int', 'bool', 'bool', 'Empty list', 'Dict', 'Tuple'])
    @allure.severity(Severity.MINOR)
    @allure.title("Пользователь с непустым, но нетекстовым значением в поле, принимающем string, не создан")
    def test_create_user_with_nums_and_bool_in_string_field(self, name: str, value: Any, api_client_users: APIClient):
        """Создает пользователя с нетекстовым, но непустым значением в поле last_name или first_name"""
        body_dict = {name: value}
        if name == 'first_name':
            body_dict['last_name'] = TestCreateUser.fake.last_name()  # заполняем обязательное поле
        request_body = self._create_body_object(**body_dict)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

    # БАГ: в документации допустимая длина текстового поля не уточняется, однако она очевидно
    # должна быть меньше 1000 слов
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize('name',
                             ['last_name', 'first_name'])
    @allure.severity(Severity.MINOR)
    @allure.title("Пользователь с длинным текстом в текстовом поле не создан")
    def test_create_user_with_long_text_in_string_field(self, name: str, api_client_users: APIClient):
        """Создает пользователя с длинным (1000 слов) текстом в обязательном поле"""
        text = TestCreateUser.fake.sentence(nb_words=1000)
        body_dict = {name: text}
        if name == 'first_name':
            body_dict['last_name'] = TestCreateUser.fake.last_name()  # заполняем обязательное поле
        request_body = self._create_body_object(**body_dict)
        response = api_client_users.post(data=request_body, headers={"Content-Type": "application/json"})

        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()

# endregion Специфика эндпойнта
