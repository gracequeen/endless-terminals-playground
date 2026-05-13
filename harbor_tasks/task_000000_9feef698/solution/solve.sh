#!/bin/bash
# Auto-generated solve script
set -e

head -20 /var/log/pods/kube-system.log
grep 'OOMKilled' /var/log/pods/kube-system.log | head -5
awk '/OOMKilled/ {split($2, a, "/"); print $1, a[2]}' /var/log/pods/kube-system.log > /home/user/oom-events.txt
cat /home/user/oom-events.txt
