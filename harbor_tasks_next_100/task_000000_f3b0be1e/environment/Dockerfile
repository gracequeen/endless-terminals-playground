FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    make \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/dataprep/scripts && \
    mkdir -p /home/user/dataprep/output

RUN echo 'print("converting...")' > /home/user/dataprep/scripts/convert.py

RUN echo "placeholder data 1" > /home/user/dataprep/output/dummy1.csv && \
    echo "placeholder data 2" > /home/user/dataprep/output/dummy2.csv

RUN chmod -R 0777 /home/user/dataprep

WORKDIR /home/user

CMD ["/bin/bash"]
