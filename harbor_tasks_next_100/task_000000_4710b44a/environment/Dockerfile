FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/translations

RUN mkdir -p /home/user/translations/en_US \
    /home/user/translations/es_ES \
    /home/user/translations/fr_FR \
    /home/user/translations/de_DE \
    /home/user/translations/ja_JP \
    /home/user/translations/zh_CN \
    /home/user/translations/ko_KR \
    /home/user/translations/pt_BR \
    /home/user/translations/it_IT \
    /home/user/translations/ru_RU \
    /home/user/translations/nl_NL \
    /home/user/translations/pl_PL \
    /home/user/translations/sv_SE \
    /home/user/translations/ar_SA \
    /home/user/translations/th_TH

# Create zh_CN with ~350MB (largest)
RUN dd if=/dev/urandom of=/home/user/translations/zh_CN/messages.po bs=1M count=150 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/zh_CN/messages.mo bs=1M count=50 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/zh_CN/fonts.dat bs=1M count=150 2>/dev/null

# Create ja_JP with ~320MB (second largest)
RUN dd if=/dev/urandom of=/home/user/translations/ja_JP/messages.po bs=1M count=140 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/ja_JP/messages.mo bs=1M count=40 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/ja_JP/fonts.dat bs=1M count=140 2>/dev/null

# Create ko_KR with ~180MB
RUN dd if=/dev/urandom of=/home/user/translations/ko_KR/messages.po bs=1M count=100 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/ko_KR/messages.mo bs=1M count=80 2>/dev/null

# Create ar_SA with ~150MB
RUN dd if=/dev/urandom of=/home/user/translations/ar_SA/messages.po bs=1M count=80 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/ar_SA/messages.mo bs=1M count=70 2>/dev/null

# Create th_TH with ~140MB
RUN dd if=/dev/urandom of=/home/user/translations/th_TH/messages.po bs=1M count=75 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/th_TH/messages.mo bs=1M count=65 2>/dev/null

# Create ru_RU with ~130MB
RUN dd if=/dev/urandom of=/home/user/translations/ru_RU/messages.po bs=1M count=70 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/ru_RU/messages.mo bs=1M count=60 2>/dev/null

# Create en_US with ~120MB
RUN dd if=/dev/urandom of=/home/user/translations/en_US/messages.po bs=1M count=65 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/en_US/messages.mo bs=1M count=55 2>/dev/null

# Create es_ES with ~110MB
RUN dd if=/dev/urandom of=/home/user/translations/es_ES/messages.po bs=1M count=60 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/es_ES/messages.mo bs=1M count=50 2>/dev/null

# Create fr_FR with ~100MB
RUN dd if=/dev/urandom of=/home/user/translations/fr_FR/messages.po bs=1M count=55 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/fr_FR/messages.mo bs=1M count=45 2>/dev/null

# Create de_DE with ~95MB
RUN dd if=/dev/urandom of=/home/user/translations/de_DE/messages.po bs=1M count=50 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/de_DE/messages.mo bs=1M count=45 2>/dev/null

# Create pt_BR with ~90MB
RUN dd if=/dev/urandom of=/home/user/translations/pt_BR/messages.po bs=1M count=50 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/pt_BR/messages.mo bs=1M count=40 2>/dev/null

# Create it_IT with ~85MB
RUN dd if=/dev/urandom of=/home/user/translations/it_IT/messages.po bs=1M count=45 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/it_IT/messages.mo bs=1M count=40 2>/dev/null

# Create nl_NL with ~75MB
RUN dd if=/dev/urandom of=/home/user/translations/nl_NL/messages.po bs=1M count=40 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/nl_NL/messages.mo bs=1M count=35 2>/dev/null

# Create pl_PL with ~70MB
RUN dd if=/dev/urandom of=/home/user/translations/pl_PL/messages.po bs=1M count=38 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/pl_PL/messages.mo bs=1M count=32 2>/dev/null

# Create sv_SE with ~60MB
RUN dd if=/dev/urandom of=/home/user/translations/sv_SE/messages.po bs=1M count=32 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/translations/sv_SE/messages.mo bs=1M count=28 2>/dev/null

RUN chmod -R 0755 /home/user/translations && \
    chmod 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
