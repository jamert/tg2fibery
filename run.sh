#!/usr/bin/env bash
docker build --tag tg2fibery:latest .
docker image prune --force
# docker-compose run --rm dev /bin/bash
docker-compose run --rm test
docker-compose down
