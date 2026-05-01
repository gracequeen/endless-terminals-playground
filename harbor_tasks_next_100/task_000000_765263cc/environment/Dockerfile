FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/qa/tests && chmod -R 0777 /home/user/qa

RUN python3.11 -m venv /home/user/qa/qa-env

RUN /home/user/qa/qa-env/bin/pip install --upgrade pip setuptools

RUN /home/user/qa/qa-env/bin/pip install requests==2.31.0

RUN mkdir -p /home/user/qa/.tox/py311

RUN python3.11 -m venv /home/user/qa/.tox/py311

RUN /home/user/qa/.tox/py311/bin/pip install --upgrade pip setuptools

RUN /home/user/qa/.tox/py311/bin/pip install pytest==7.4.0

RUN if [ -f /home/user/qa/qa-env/bin/pytest ]; then rm /home/user/qa/qa-env/bin/pytest; fi

RUN cat > /home/user/qa/requirements.txt << 'EOF'
requests==2.31.0
pytest==7.4.0
EOF

RUN cat > /home/user/qa/tests/test_api.py << 'EOF'
import requests

def test_api_reachable():
    # Just verifies imports work; doesn't hit network
    assert hasattr(requests, 'get')
    assert callable(requests.get)
EOF

RUN touch /home/user/qa/tests/__init__.py

RUN chmod -R 0777 /home/user/qa

RUN chown -R 1000:1000 /home/user

WORKDIR /home/user/qa

ENV PATH="/home/user/qa/qa-env/bin:/home/user/qa/.tox/py311/bin:/usr/local/bin:/usr/bin:/bin"
ENV VIRTUAL_ENV="/home/user/qa/qa-env"

USER 1000

CMD ["/bin/bash"]
