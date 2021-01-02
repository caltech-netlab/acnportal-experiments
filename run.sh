#!/bin/bash

docker run --rm -p 8890:8888 -e JUPYTER_ENABLE_LAB=yes -v "$PWD":/home/jovyan/work acn-sim-demo:latest