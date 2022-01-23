#!/usr/bin/env bash
docker build --tag tg2fibery:latest .
docker-compose run --rm app /bin/bash
docker image prune --force
