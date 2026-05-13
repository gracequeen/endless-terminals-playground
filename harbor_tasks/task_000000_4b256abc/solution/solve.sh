#!/bin/bash
# Auto-generated solve script
set -e

find /home/user/deploy -type f | head -50
cd /home/user/deploy && ./render.py staging web-api
cat /home/user/deploy/overrides/staging/web-api.yaml
cat /home/user/deploy/environments/staging.yaml
cat /home/user/deploy/base/defaults.yaml
cat /home/user/deploy/services/web-api.yaml
cat /home/user/deploy/overrides/production/web-api.yaml
cat /home/user/deploy/overrides/.legacy/web-api.yaml
cat /home/user/deploy/render.py
cat /home/user/deploy/environments/production.yaml
mv /home/user/deploy/overrides/.legacy/web-api.yaml /home/user/deploy/overrides/.legacy/web-api.yaml.disabled
cd /home/user/deploy && ./render.py staging web-api
cd /home/user/deploy && ./render.py production web-api
