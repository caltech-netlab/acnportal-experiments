#!/bin/bash

docker build -t acnportal_experiments:latest .
docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v "$PWD":/home/jovyan/work acnportal_experiments:latest