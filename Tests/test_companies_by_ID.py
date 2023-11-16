"""API-тесты для эндпойнта /api/companies/{company_id}"""

from random import randint
from typing import Union

import allure
import pytest
from allure_commons.types import Severity
from pytest_check import check

# Элементы проекта
from Data import json_schemas
from Helpers.api_client import APIClient
from base_tests import BaseStatusHeadersSchemaTests


@allure.parent_suite("/api/companies/{company_id}")
@allure.suite("Базовый запрос с указанием ID компании")
class TestGetCompanyByID:
    """Проверяет результат запроса с параметром 'ID компании'.
    Известно, что в базе всего 7 объектов
    """

    @pytest.mark.smoke
    @allure.title("Запрос с валидным ID компании в пределах фактического количества объектов")
    @allure.severity(Severity.BLOCKER)
    def test_company_with_valid_id_within_range(self, api_client: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'ID компании', В ПРЕДЕЛАХ
        фактического количества объектов в базе (7)
        """
        company_id = randint(1, 7)
        response = api_client.get(path=f"/{company_id}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANY_BY_ID, 200)
        tester.test_status_headers_schema()

        body = response.json()
        check.equal(body["company_id"], company_id,
                    f"ID компании в ответе ({body['company_id']}) не соответствует "
                    f"ID компании в запросе ({company_id})")

        first_lang = body['description_lang'][0]['translation_lang']
        check.equal(first_lang, 'EN',
                    f"При невыбранной локализации первым должен быть показан EN; в ответе {first_lang}")

    @pytest.mark.smoke
    @pytest.mark.parametrize('id_without_range', [0, randint(8, 100)])
    @allure.title("""Запрос с валидным ID компании вне пределов фактического количества объектов
     в БД ({id_without_range})""")
    @allure.severity(Severity.NORMAL)
    def test_company_with_valid_id_without_range(self, id_without_range: int, api_client: APIClient):
        """
        Проверяет результат запроса с ВАЛИДНЫМ параметром 'ID компании', РАВНЫМ 0 ИЛИ ПРЕВЫШАЮЩИМ
        фактическое число объектов в базе
        """
        response = api_client.get(path=f"/{id_without_range}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.NOT_FOUND_404, 404)
        tester.test_status_headers_schema()

    # БАГ с параметром -1: невалидный ID дает в ответе 404 вместо 422
    @pytest.mark.negative
    @pytest.mark.regression
    @pytest.mark.parametrize('invalid_id', ['ABC', 1.5, -1])
    @allure.title("Запрос с невалидным ID ({invalid_id})")
    @allure.severity(Severity.MINOR)
    def test_company_with_invalid_id(self, invalid_id: Union[str, float, int], api_client: APIClient):
        """Проверяет результат запроса с НЕВАЛИДНЫМ параметром 'ID компании'"""
        response = api_client.get(path=f"/{invalid_id}")
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.UNPROCESSABLE_ENTITY_422, 422)
        tester.test_status_headers_schema()


@pytest.mark.smoke
@allure.parent_suite("/api/companies/{company_id}")
@allure.suite("Запрос по ID компании с указанием локализации в хедере")
class TestGetCompanyByIDWithLocalization:
    """
    Проверяет результат запроса с параметром 'ID компании' и указанием локализации в хедере.
    Варианты локализации доступны только для компании с ID=1, поэтому тестируем только с ID=1
    """

    @pytest.mark.parametrize('localization, starts_with',
                             [('RU', 'Ее сздать'), ('PL', 'Podkomorzynę'), ('EN', 'Ye on properly'),
                              ('UA', 'Ой у лузі')])
    @allure.title("Запрос  на /api/companies/1 с указанием валидной локализации ({localization})")
    @allure.severity(Severity.NORMAL)
    def test_company_with_valid_localization(self, localization: str, starts_with: str, api_client: APIClient):
        """Проверяет результат запроса для компании с ID=1 с указанием ВАЛИДНОЙ локализации в хедере"""
        response = api_client.get(path="/1", headers={'Accept-Language': f'{localization}'})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANY_BY_ID, 200)
        tester.test_status_headers_schema()

        body = response.json()
        check.equal(body["company_id"], 1,
                    f"ID компании в ответе ({body['company_id']}) не соответствует ID компании в запросе (1)")

        description = body['description']
        check.is_true(description.startswith(starts_with),
                      f"Локализация в ответе не соответствует запросу ({localization})")

    @pytest.mark.negative
    @allure.title("Запрос на /api/companies/1 с указанием невалидной локализации (XXX)")
    @allure.severity(Severity.NORMAL)
    def test_company_with_invalid_localization(self, api_client: APIClient):
        """
        Проверяет результат запроса для компании с ID=1 с указанием НЕВАЛИДНОЙ локализации в хедере.
        Считаем ОР, когда в ответе все доступные варианты локализации, как будто локализация не указана.
        В документации не уточняется.
        """
        response = api_client.get(path="/1", headers={'Accept-Language': 'XXX'})
        tester = BaseStatusHeadersSchemaTests(response, json_schemas.COMPANY_BY_ID, 200)
        tester.test_status_headers_schema()

        body = response.json()
        check.equal(body["company_id"], 1,
                    f"ID компании в ответе ({body['company_id']}) не соответствует ID компании в запросе (1)")

        descriptions = body['description_lang']
        check.equal(len(descriptions), 4,
                    f"В ответе не все варианты локализации: {len(descriptions)} вместо 4")
