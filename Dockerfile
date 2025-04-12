FROM python:3.13-alpine3.21

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY entrypoint.sh .
COPY . .

EXPOSE 8000