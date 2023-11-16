from collections import Counter

import pytest
import requests

from Data.constants import BASE_URL_COMPANIES, BASE_URL_COMPANIES_HTTP
from Helpers.api_client import APIClient


@pytest.fixture(scope='module')
def api_client() -> APIClient:
    """Возвращает базовый API-клиент по BASE_URL_COMPANIES"""
    return APIClient(base_url=BASE_URL_COMPANIES)


@pytest.fixture(scope='class')
def response_get_base_url(api_client) -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_COMPANIES"""
    return api_client.get()


@pytest.fixture(scope='class')
def response_with_http() -> requests.Response:
    """Возвращает результат GET-запроса без параметров на BASE_URL_COMPANIES_HTTP"""
    unsecure_api_client = APIClient(base_url=BASE_URL_COMPANIES_HTTP)
    return unsecure_api_client.get()


@pytest.fixture(scope='function')
def total_status_counter(api_client) -> Counter:
    """
    По результатам запроса на /api/companies/ с лимитом 7 составляет и возвращает словарь с общим количеством компаний
    для каждого из статусов. Словарь используется для проверки работы фильтра по статусу компании.
    """
    response = api_client.get(path=f"/?limit=7")  # Известно, что в базе всего 7 компаний
    body = response.json()
    data = body['data']
    # Убеждаемся, что все объекты из базы получены
    assert len(data) == 7, f"В ответе не все компании: {len(data)} вместо 7"
    return Counter(company['company_status'] for company in data)
