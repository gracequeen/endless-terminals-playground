FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    gawk \
    sed \
    vim \
    nano \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/pentest && chmod 0777 /home/user && chmod 0777 /home/user/pentest

RUN cat <<'EOF' > /home/user/pentest/target_iptables.txt
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -p tcp --dport 22 -j ACCEPT
-A INPUT -p tcp --dport 80 -m string --string "Mozilla" --algo bm -j ACCEPT
-A INPUT -p tcp --dport 443 -m string --string "Mozilla" --algo bm -j ACCEPT
-A INPUT -p tcp --dport 80 -j DROP
-A INPUT -p tcp --dport 443 -j DROP
-A INPUT -p icmp --icmp-type echo-request -j ACCEPT
COMMIT
EOF

RUN chmod 644 /home/user/pentest/target_iptables.txt

RUN useradd -m -d /home/user -s /bin/bash user && chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
