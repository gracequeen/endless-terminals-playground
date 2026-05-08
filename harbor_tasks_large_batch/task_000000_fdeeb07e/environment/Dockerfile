FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/.cache/pip/wheels/aa/bb/cc \
    && mkdir -p /home/user/.cache/pip/wheels/dd/ee/ff \
    && mkdir -p /home/user/.cache/pip/http/cache1 \
    && mkdir -p /home/user/.cache/pip/http/cache2 \
    && mkdir -p /home/user/.cache/fontconfig

RUN dd if=/dev/urandom of=/home/user/.cache/pip/wheels/aa/bb/cc/numpy-1.24.0-cp310-cp310-linux_x86_64.whl bs=1M count=50 2>/dev/null || true \
    && dd if=/dev/urandom of=/home/user/.cache/pip/wheels/aa/bb/cc/pandas-2.0.0-cp310-cp310-linux_x86_64.whl bs=1M count=80 2>/dev/null || true \
    && dd if=/dev/urandom of=/home/user/.cache/pip/wheels/dd/ee/ff/scipy-1.10.0-cp310-cp310-linux_x86_64.whl bs=1M count=100 2>/dev/null || true \
    && dd if=/dev/urandom of=/home/user/.cache/pip/wheels/dd/ee/ff/matplotlib-3.7.0-cp310-cp310-linux_x86_64.whl bs=1M count=70 2>/dev/null || true \
    && dd if=/dev/urandom of=/home/user/.cache/pip/http/cache1/requests_cache_data bs=1M count=30 2>/dev/null || true \
    && dd if=/dev/urandom of=/home/user/.cache/pip/http/cache2/urllib3_cache_data bs=1M count=20 2>/dev/null || true

RUN echo "fontconfig cache data" > /home/user/.cache/fontconfig/cache-data.txt

RUN chown -R 1000:1000 /home/user \
    && chmod -R 0755 /home/user/.cache \
    && chmod 0777 /home/user/.cache/pip \
    && chmod -R 0777 /home/user/.cache/pip

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
