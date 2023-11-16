"""Вспомогательные инструменты для проекта API_tests_example"""

import csv
from pathlib import Path


class Helpers:
    """Вспомогательные инструменты для проекта"""

    @staticmethod
    def get_test_data_from_csv(file_name):
        """Парсит файл csv и возвращает список значений построчно"""
        path = Path(__file__).parents[1].joinpath('Data').joinpath(file_name)
        with open(path, 'rt') as f:
            reader = csv.reader(f, delimiter=',')
            return [*reader]  # [[line10, line11], [line20, line21]...]
