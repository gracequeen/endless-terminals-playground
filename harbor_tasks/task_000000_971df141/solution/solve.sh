#!/bin/bash
# Auto-generated solve script
set -e

find /home/user/captures -name "*.perf" -type f
find /home/user/captures -mindepth 2 -name "*.perf" -type f -exec mv {} /home/user/captures/ \;
ls -la /home/user/captures/*.perf
find /home/user/captures -mindepth 2 -name "*.perf" -type f
