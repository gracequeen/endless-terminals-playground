FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

RUN pip3 install --upgrade pip pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/testenv && \
    mkdir -p /home/user/pypi-mirror/simple/numpy && \
    mkdir -p /home/user/pypi-mirror/simple/pandas && \
    mkdir -p /home/user/pypi-mirror/simple/python-dateutil && \
    mkdir -p /home/user/pypi-mirror/simple/pytz && \
    mkdir -p /home/user/pypi-mirror/simple/six && \
    mkdir -p /home/user/pypi-mirror/simple/tzdata && \
    mkdir -p /home/user/pypi-mirror/packages && \
    mkdir -p /home/user/.pip

RUN pip3 download --no-deps --dest /tmp/wheels \
    numpy==1.24.3 \
    pandas==2.0.2 \
    python-dateutil==2.8.2 \
    pytz==2023.3 \
    six==1.16.0 \
    tzdata==2023.3

RUN cp /tmp/wheels/numpy-1.24.3-*.whl /home/user/pypi-mirror/packages/numpy-1.24.3-cp311-cp311-linux_x86_64.whl 2>/dev/null || \
    cp /tmp/wheels/numpy-1.24.3*.whl /home/user/pypi-mirror/packages/numpy-1.24.3-cp311-cp311-linux_x86_64.whl

RUN cp /tmp/wheels/pandas-2.0.2-*.whl /home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl 2>/dev/null || \
    cp /tmp/wheels/pandas-2.0.2*.whl /home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl

RUN cp /tmp/wheels/python_dateutil-2.8.2-py2.py3-none-any.whl /home/user/pypi-mirror/packages/ && \
    cp /tmp/wheels/pytz-2023.3-py2.py3-none-any.whl /home/user/pypi-mirror/packages/ && \
    cp /tmp/wheels/six-1.16.0-py2.py3-none-any.whl /home/user/pypi-mirror/packages/ && \
    cp /tmp/wheels/tzdata-2023.3-py2.py3-none-any.whl /home/user/pypi-mirror/packages/

RUN rm -rf /tmp/wheels

RUN NUMPY_SHA=$(sha256sum /home/user/pypi-mirror/packages/numpy-1.24.3-cp311-cp311-linux_x86_64.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for numpy</title></head><body><h1>Links for numpy</h1><a href=\"../../packages/numpy-1.24.3-cp311-cp311-linux_x86_64.whl#sha256=${NUMPY_SHA}\" data-requires-python=\">=3.9\">numpy-1.24.3-cp311-cp311-linux_x86_64.whl</a></body></html>" > /home/user/pypi-mirror/simple/numpy/index.html

RUN PANDAS_SHA=$(sha256sum /home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for pandas</title></head><body><h1>Links for pandas</h1><a href=\"../../packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl#sha256=${PANDAS_SHA}\" data-requires-python=\">=3.9\" data-core-metadata=\"sha256=abc123\">pandas-2.0.2-cp311-cp311-linux_x86_64.whl</a></body></html>" > /home/user/pypi-mirror/simple/pandas/index.html

RUN cat > /home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl.metadata << 'METAEOF'
Metadata-Version: 2.1
Name: pandas
Version: 2.0.2
Requires-Python: >=3.9
Requires-Dist: numpy>=2.0.0
Requires-Dist: python-dateutil>=2.8.2
Requires-Dist: pytz>=2020.1
Requires-Dist: tzdata>=2022.1
METAEOF

RUN DATEUTIL_SHA=$(sha256sum /home/user/pypi-mirror/packages/python_dateutil-2.8.2-py2.py3-none-any.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for python-dateutil</title></head><body><h1>Links for python-dateutil</h1><a href=\"../../packages/python_dateutil-2.8.2-py2.py3-none-any.whl#sha256=${DATEUTIL_SHA}\" data-requires-python=\">=2.7\">python_dateutil-2.8.2-py2.py3-none-any.whl</a></body></html>" > /home/user/pypi-mirror/simple/python-dateutil/index.html

RUN PYTZ_SHA=$(sha256sum /home/user/pypi-mirror/packages/pytz-2023.3-py2.py3-none-any.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for pytz</title></head><body><h1>Links for pytz</h1><a href=\"../../packages/pytz-2023.3-py2.py3-none-any.whl#sha256=${PYTZ_SHA}\">pytz-2023.3-py2.py3-none-any.whl</a></body></html>" > /home/user/pypi-mirror/simple/pytz/index.html

RUN SIX_SHA=$(sha256sum /home/user/pypi-mirror/packages/six-1.16.0-py2.py3-none-any.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for six</title></head><body><h1>Links for six</h1><a href=\"../../packages/six-1.16.0-py2.py3-none-any.whl#sha256=${SIX_SHA}\" data-requires-python=\">=2.7\">six-1.16.0-py2.py3-none-any.whl</a></body></html>" > /home/user/pypi-mirror/simple/six/index.html

RUN TZDATA_SHA=$(sha256sum /home/user/pypi-mirror/packages/tzdata-2023.3-py2.py3-none-any.whl | cut -d' ' -f1) && \
    echo "<!DOCTYPE html><html><head><title>Links for tzdata</title></head><body><h1>Links for tzdata</h1><a href=\"../../packages/tzdata-2023.3-py2.py3-none-any.whl#sha256=${TZDATA_SHA}\" data-requires-python=\">=2\">tzdata-2023.3-py2.py3-none-any.whl</a></body></html>" > /home/user/pypi-mirror/simple/tzdata/index.html

RUN echo '<!DOCTYPE html><html><head><title>Simple Index</title></head><body><h1>Simple Index</h1><a href="numpy/">numpy</a><br/><a href="pandas/">pandas</a><br/><a href="python-dateutil/">python-dateutil</a><br/><a href="pytz/">pytz</a><br/><a href="six/">six</a><br/><a href="tzdata/">tzdata</a><br/></body></html>' > /home/user/pypi-mirror/simple/index.html

RUN cat > /home/user/testenv/requirements.txt << 'EOF'
numpy==1.24.3
pandas==2.0.2
EOF

RUN cat > /home/user/.pip/pip.conf << 'EOF'
[global]
index-url = file:///home/user/pypi-mirror/simple
no-index = false
trusted-host = 
EOF

RUN python3 -m venv /home/user/testenv/venv

RUN /home/user/testenv/venv/bin/pip install --upgrade pip

RUN chown -R 1000:1000 /home/user && \
    chmod -R 0777 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
