# syntax=docker/dockerfile:1

FROM python:3.11
WORKDIR ~/tmp/API
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN chmod o+x ./start_tests.sh
ENTRYPOINT ["./start_tests.sh"]