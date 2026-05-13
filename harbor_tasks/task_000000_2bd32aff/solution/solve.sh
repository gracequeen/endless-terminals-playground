#!/bin/bash
# Auto-generated solve script
set -e

gpg --decrypt /home/user/evidence/packet_dump.tar.gz.gpg > /home/user/evidence/packet_dump.tar.gz
gpg --verify /home/user/evidence/packet_dump.tar.gz.sig /home/user/evidence/packet_dump.tar.gz
mkdir -p /home/user/evidence/extracted && tar -xzf /home/user/evidence/packet_dump.tar.gz -C /home/user/evidence/extracted
ls -la /home/user/evidence/extracted/
ls -la /home/user/evidence/extracted/captures/
