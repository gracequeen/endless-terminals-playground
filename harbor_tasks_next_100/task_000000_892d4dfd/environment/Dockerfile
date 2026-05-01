FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/tracking && chmod 0777 /home/user && chmod 0777 /home/user/tracking

RUN cat <<EOF > /home/user/tracking/requirements.txt
numpy==1.24.3
pandas>=2.0,<3.0
mlflow>=2.0
scikit-learn==1.3.0
boto3>=1.28.0
EOF

RUN chmod 0666 /home/user/tracking/requirements.txt

WORKDIR /home/user

CMD ["/bin/bash"]
