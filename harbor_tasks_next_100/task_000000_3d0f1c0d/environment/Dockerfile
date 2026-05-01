FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

WORKDIR /home/user

RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test User"

RUN mkdir -p /home/user/assets-repo && \
    cd /home/user/assets-repo && \
    git init

RUN cd /home/user/assets-repo && \
    head -c 150000 /dev/urandom > image1.png && \
    head -c 200000 /dev/urandom > image2.png && \
    git add image1.png image2.png && \
    git commit -m "Initial commit with two png files"

RUN cd /home/user/assets-repo && \
    head -c 180000 /dev/urandom > image3.png && \
    git add image3.png && \
    git commit -m "Add third png file"

RUN cd /home/user/assets-repo && \
    head -c 120000 /dev/urandom > image4.png && \
    git rm image1.png && \
    git add image4.png && \
    git commit -m "Remove image1 and add image4"

RUN cd /home/user/assets-repo && \
    head -c 197392 /dev/urandom > image5.png && \
    git add image5.png && \
    git commit -m "Add fifth png file"

RUN cd /home/user/assets-repo && \
    git rm image2.png && \
    git commit -m "Remove image2"

RUN chmod -R 0755 /home/user/assets-repo && \
    chmod 0777 /home/user

CMD ["/bin/bash"]
