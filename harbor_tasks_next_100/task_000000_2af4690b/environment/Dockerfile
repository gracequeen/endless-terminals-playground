FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test User"

WORKDIR /home/user/webapp

RUN git init

RUN cat <<'EOF' > /home/user/webapp/.gitmodules
[submodule "vendor/loglib"]
	path = vendor/loglib
	url = https://github.com/gabime/spdlog.git
EOF

RUN echo "# Webapp Project" > /home/user/webapp/README.md

RUN git add .gitmodules README.md && \
    git commit -m "Initial commit with submodule configuration"

RUN chmod -R 0777 /home/user/webapp

WORKDIR /home/user
