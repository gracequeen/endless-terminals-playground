FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN cat > /home/user/.bashrc << 'EOF'
# ~/.bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific aliases
alias ll='ls -la'
alias grep='grep --color=auto'

# Custom prompt
PS1='\u@\h:\w\$ '
EOF

RUN chmod 0666 /home/user/.bashrc

RUN useradd -d /home/user -s /bin/bash user || true

WORKDIR /home/user

CMD ["/bin/bash"]
