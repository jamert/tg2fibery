#!/usr/bin/env bash
docker build --tag tg2fibery:latest .
docker run --rm --mount type=bind,source="$(pwd)",target=/root -it tg2fibery /bin/bash
