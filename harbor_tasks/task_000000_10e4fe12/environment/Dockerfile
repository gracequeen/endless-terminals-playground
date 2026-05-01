FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    gawk \
    sed \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -u 1000 -s /bin/bash user

RUN mkdir -p /home/user/projects/alpha \
    && mkdir -p /home/user/projects/beta \
    && mkdir -p /home/user/projects/gamma/subdir \
    && mkdir -p /home/user/projects/delta \
    && mkdir -p /home/user/backups

RUN echo -n "alpha config" > /home/user/projects/alpha/config.json \
    && chown user:user /home/user/projects/alpha/config.json \
    && chmod 644 /home/user/projects/alpha/config.json

RUN echo -n "alpha secret" > /home/user/projects/alpha/secret.key \
    && chown root:root /home/user/projects/alpha/secret.key \
    && chmod 600 /home/user/projects/alpha/secret.key

RUN echo -n "beta,data,here" > /home/user/projects/beta/data.csv \
    && chown user:user /home/user/projects/beta/data.csv \
    && chmod 644 /home/user/projects/beta/data.csv

RUN echo -n "beta notes" > /home/user/projects/beta/notes.txt \
    && chown user:user /home/user/projects/beta/notes.txt \
    && chmod 644 /home/user/projects/beta/notes.txt

RUN echo -n "deep file" > /home/user/projects/gamma/subdir/deep.txt \
    && chown user:user /home/user/projects/gamma/subdir/deep.txt \
    && chmod 644 /home/user/projects/gamma/subdir/deep.txt

RUN echo -n "gamma readme" > /home/user/projects/gamma/readable.md \
    && chown user:user /home/user/projects/gamma/readable.md \
    && chmod 644 /home/user/projects/gamma/readable.md

RUN echo -n "gamma locked" > /home/user/projects/gamma/locked.dat \
    && chown root:root /home/user/projects/gamma/locked.dat \
    && chmod 600 /home/user/projects/gamma/locked.dat

RUN echo -n "forbidden" > /home/user/projects/delta/forbidden.txt \
    && chown root:root /home/user/projects/delta/forbidden.txt \
    && chmod 644 /home/user/projects/delta/forbidden.txt

RUN chown user:user /home/user/projects/alpha \
    && chmod 755 /home/user/projects/alpha

RUN chown user:user /home/user/projects/beta \
    && chmod 711 /home/user/projects/beta

RUN chown user:user /home/user/projects/gamma \
    && chmod 755 /home/user/projects/gamma

RUN chown user:user /home/user/projects/gamma/subdir \
    && chmod 755 /home/user/projects/gamma/subdir

RUN chown root:root /home/user/projects/delta \
    && chmod 700 /home/user/projects/delta

RUN chown user:user /home/user/projects \
    && chmod 755 /home/user/projects

RUN chown user:user /home/user/backups \
    && chmod 755 /home/user/backups

RUN chmod 0777 /home/user

USER user
WORKDIR /home/user
