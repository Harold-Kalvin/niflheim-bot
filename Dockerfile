FROM python:3.13.2-alpine3.21

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ./app /app

WORKDIR /app

RUN adduser --disabled-password appuser
USER appuser

CMD ["python", "-u", "main.py"]
