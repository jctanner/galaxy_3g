#!/bin/bash

export PYTHONUNBUFFERED=1

while true; do
    /venv/bin/python app.py
    sleep 2
done
