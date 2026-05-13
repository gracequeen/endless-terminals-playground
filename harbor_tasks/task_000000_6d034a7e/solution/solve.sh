#!/bin/bash
# Auto-generated solve script
set -e

ls -la /home/user/ingest/
cat /home/user/ingest/checksums.sha256
ls -la /home/user/ingest/packages/
cat /home/user/ingest/verify.sh
cd /home/user/ingest/packages && sha256sum -c ../checksums.sha256
cd /home/user/ingest/packages && sha256sum *.tar.gz
sed -i 's/Beta-3.0.tar.gz/beta-3.0.tar.gz/; s/Delta-0.9.tar.gz/delta-0.9.tar.gz/; s/Epsilon-1.0.tar.gz/epsilon-1.0.tar.gz/' /home/user/ingest/checksums.sha256
cat /home/user/ingest/checksums.sha256
cd /home/user/ingest/packages && sha256sum -c ../checksums.sha256
/home/user/ingest/verify.sh
