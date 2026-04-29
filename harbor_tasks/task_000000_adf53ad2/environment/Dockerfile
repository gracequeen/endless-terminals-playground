FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3 \
    python3-pip \
    curl \
    && add-apt-repository -y ppa:git-core/ppa \
    && apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN touch /var/log/git-hooks.log && chmod 0666 /var/log/git-hooks.log

RUN useradd -m -d /home/user -s /bin/bash user

WORKDIR /home/user

RUN git config --global user.email "user@example.com" && \
    git config --global user.name "Test User" && \
    git config --global init.defaultBranch main

RUN mkdir -p /home/user/project && \
    cd /home/user/project && \
    git init && \
    for i in 1 2 3 4 5 6 7 8 9 10; do \
        echo "Content for commit $i" > "file$i.txt" && \
        git add "file$i.txt" && \
        git commit -m "Commit number $i"; \
    done

RUN git clone --bare /home/user/project /home/user/project.git

RUN cd /home/user/project && \
    git remote add origin /home/user/project.git

RUN cat > /home/user/project/.git/hooks/pre-push << 'EOF'
#!/bin/bash
cd /srv/repos/project
HASH=$(git rev-parse --verify HEAD)
echo "$(date): push verified, HEAD=$HASH" >> /var/log/git-hooks.log
exit 0
EOF

RUN chmod 755 /home/user/project/.git/hooks/pre-push

RUN chown -R user:user /home/user/project /home/user/project.git

USER user

WORKDIR /home/user

CMD ["/bin/bash"]
