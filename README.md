### API тесты на стеке **Python + pytest + requests** для учебного ресурса https://send-request.me/.

#### *Work in progress :)*

---

##### Проверяются эндпойнты:

- /api/companies/,
- /api/companies/{company_id}  
- /api/users  
  *(список дополняется)*

##### Окружение разработки:

- Linux Ubuntu 23.04
- Python 3.11
- Docker 20.10.17
- Allure 2.24.1

##### Зависимости:

- `requirements.txt`
- для запуска в контейнере - Docker
- для просмотра отчетов - Allure (не добавляется в образ, ожидается на хосте)

##### Запуск тестов локально без Docker:

1. Создать и активировать виртуальное окружение.
2. Установить зависимости из `requirements.txt` через pip.
3. Запустить тесты:  
   `pytest <путь до проекта>/Tests/ [-m <метка>] [-n <CPUs>] --clean-alluredir --alluredir=<директория для файлов отчета>`

##### Запуск тестов через Docker из корневой директории проекта:

1. Собрать образ из Dockerfile:  
`docker build -t <имя образа> .`
2. Запустить контейнер из образа:
    - с сохранением отчетов Allure после выхода из контейнера:  
      `docker run --name <имя контейнера> --mount source=<имя volume для сохранения отчетов Allure>,target=<директория для
      файлов отчета Allure в контейнере> <имя образа>`
    - без сохранения отчетов Allure после выхода из контейнера:  
      `docker run --name <имя контейнера> <имя образа>`

##### Просмотр отчета Allure:

- разовый просмотр:  
  `allure serve <директория для файлов отчета>`

- собрать отчет для последующего просмотра:  
  `allure generate  <директория для файлов отчета>`  
  `allure open  <директория сгенерированного отчета>`  
