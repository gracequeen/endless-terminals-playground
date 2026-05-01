FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/webapp && chmod 0777 /home/user && chmod 0777 /home/user/webapp

RUN printf 'DATABASE_URL=postgres://localhost:5432/webapp\nSTRIPE_SECRET_KEY=sk_live_OLD_COMPROMISED_KEY\nREDIS_HOST=127.0.0.1\nDEBUG=false\n' > /home/user/webapp/.env

RUN chmod 0666 /home/user/webapp/.env

WORKDIR /home/user

CMD ["/bin/bash"]
