#!/bin/bash
# Auto-generated solve script
set -e

find /var/data -type f -size +100M -printf '%s %p\n' 2>/dev/null | sort -rn | awk '{printf "%.1fM %s\n", $1/1024/1024, $2}' > /home/user/big_files.txt
cat /home/user/big_files.txt
