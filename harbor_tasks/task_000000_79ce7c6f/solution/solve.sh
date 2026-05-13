#!/bin/bash
# Auto-generated solve script
set -e

python3 -m venv /home/user/webapp/venv
/home/user/webapp/venv/bin/pip install -r /home/user/webapp/requirements.txt
/home/user/webapp/venv/bin/pip list | grep -E "flask|gunicorn"
/home/user/webapp/venv/bin/pip list | grep -iE "flask|gunicorn"
