# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster
WORKDIR /root/

# docker run --rm --mount type=bind,source="$(pwd)",target=/root $(docker build -q .) CMD
