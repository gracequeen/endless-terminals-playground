FROM ubuntu:22.04
RUN sed -i "s|archive.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g; s|security.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g" /etc/apt/sources.list 2>/dev/null || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/deploy && chmod 0777 /home/user && chmod 0777 /home/user/deploy

RUN cat <<EOF > /home/user/deploy/requirements.txt
pandas>=2.0.0
numpy
scikit-learn>=1.2.0
matplotlib>=3.7.0
requests>=2.28.0
EOF

RUN chmod 0666 /home/user/deploy/requirements.txt
