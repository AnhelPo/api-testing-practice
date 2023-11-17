from collections import defaultdict

import pytest
import requests

from Data.constants import *
from Helpers.api_client import APIClient


@pytest.fixture(scope='module')
def api_client_companies() -> APIClient:
    """Возвращает базовый API-клиент по BASE_URL_COMPANIES"""
    return APIClient(base_url=BASE_URL_COMPANIES)


@pytest.fixture(scope='class')
def response_get_base_companies(api_client_companies) -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_COMPANIES"""
    return api_client_companies.get()


@pytest.fixture(scope='class')
def response_companies_with_http() -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_COMPANIES_HTTP"""
    unsecure_api_client = APIClient(base_url=BASE_URL_COMPANIES_HTTP)
    return unsecure_api_client.get()


@pytest.fixture(scope='module')
def api_client_users() -> APIClient:
    """Возвращает базовый API-клиент по BASE_URL_USERS"""
    return APIClient(base_url=BASE_URL_USERS)


@pytest.fixture(scope='class')
def response_get_base_users(api_client_users) -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_USERS"""
    return api_client_users.get()


@pytest.fixture(scope='class')
def response_users_with_http() -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_USERS_HTTP"""
    unsecure_api_client = APIClient(base_url=BASE_URL_USERS_HTTP)
    return unsecure_api_client.get()


@pytest.fixture(scope='function')
def companies_grouped_by_statuses(api_client_companies) -> dict:
    """
    По результатам запроса на /api/companies/ с лимитом 7 составляет и возвращает словарь статусов
    и соответствующих им списков ID компаний
    """
    response = api_client_companies.get(path=f"/?limit=7")  # Известно, что в базе всего 7 компаний
    body = response.json()
    data = body['data']
    # Убеждаемся, что все объекты из базы получены
    assert len(data) == 7, f"В ответе не все компании: {len(data)} вместо 7"
    counter = defaultdict(list)
    for company in data:
        counter[company['company_status']].append(company['company_id'])
    return counter
