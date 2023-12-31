# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster
WORKDIR /root/

# development only
RUN pip install pip-tools
# TODO: sync shell history between rebuilds

COPY requirements*.txt .
RUN pip-sync requirements*.txt
COPY . .
RUN pip install -e .
