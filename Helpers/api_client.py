"""API-клиент для проекта API_tests_example"""

import requests
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type


class APIClient:
    """
    Клиент для работы с API. Инициализируется базовым url, на который пойдут запросы
    """

    def __init__(self, base_url):
        self.base_url = base_url

    # Конкретно этот API иногда тормозит, поэтому реализован перезапуск
    @retry(retry=retry_if_exception_type(requests.exceptions.Timeout), wait=wait_fixed(0.5),
           reraise=True, stop=stop_after_attempt(3))
    def get(self, path="/", params=None, headers=None, timeout=0.5, allow_redirects=False):
        """Отправляет get-запрос на указанный адрес"""
        return requests.get(url=f"{self.base_url}{path}",
                            params=params, headers=headers,
                            timeout=timeout, allow_redirects=allow_redirects)

    def post(self, path="/", params=None, data=None, headers=None, timeout=1, allow_redirects=False):
        """Отправляет post-запрос на указанный адрес"""
        return requests.post(url=f"{self.base_url}{path}",
                             params=params, data=data, headers=headers,
                             timeout=timeout, allow_redirects=allow_redirects)

    def delete(self, path="/", params=None, data=None, headers=None, timeout=0.5, allow_redirects=False):
        """Отправляет delete-запрос на указанный адрес"""
        return requests.delete(url=f"{self.base_url}{path}",
                               params=params, data=data, headers=headers,
                               timeout=timeout, allow_redirects=allow_redirects)
