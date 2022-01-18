# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster
WORKDIR /root/

# development only
RUN python -m pip install pip-tools

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
