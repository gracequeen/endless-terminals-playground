FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/deploy && chmod 0777 /home/user/deploy

RUN mkdir -p /home/user/releases/v2.3.9 && chmod 0777 /home/user/releases/v2.3.9
RUN mkdir -p /home/user/releases/v2.4.1 && chmod 0777 /home/user/releases/v2.4.1
RUN chmod 0777 /home/user/releases

RUN echo "v2.3.9" > /home/user/releases/v2.3.9/marker.txt
RUN echo "v2.4.1" > /home/user/releases/v2.4.1/marker.txt

RUN ln -s /home/user/releases/v2.3.9 /home/user/deploy/current

RUN useradd -m -d /home/user -s /bin/bash user && chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
