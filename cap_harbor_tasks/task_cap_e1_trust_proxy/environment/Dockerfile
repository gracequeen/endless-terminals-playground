FROM node:20-slim

RUN apt-get update && apt-get install -y git python3 python3-pip patch && \
    pip3 install pytest --break-system-packages && \
    rm -rf /var/lib/apt/lists/*

# TODO: replace with repo at base_commit (not main snapshot)
# The repo should be at the state BEFORE non_test_patch is applied,
# but AFTER test_patch is applied so tests exist and fail.
#
# Build-time steps (once base_commit is resolved):
#   COPY app-generation-gateway-<base_commit>/ /home/user/app-generation-gateway/
#   COPY patches/AP-AC-Products-Services__app-generation-gateway-24.test.patch /tmp/test.patch
#   RUN cd /home/user/app-generation-gateway && git apply /tmp/test.patch
COPY app-generation-gateway/ /home/user/app-generation-gateway/

RUN cd /home/user/app-generation-gateway && npm install --ignore-scripts

WORKDIR /home/user/app-generation-gateway
