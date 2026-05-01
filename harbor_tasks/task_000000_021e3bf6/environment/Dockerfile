FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bash \
    gawk \
    sed \
    grep \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/memstats && chmod 0777 /home/user && chmod 0777 /home/user/memstats

RUN cat <<'EOF' > /home/user/memstats/host01.txt
MemTotal:       16384000 kB
MemFree:         2048000 kB
MemAvailable:    8192000 kB
Buffers:          512000 kB
Cached:          4096000 kB
SwapCached:            0 kB
Active:          8192000 kB
Inactive:        4096000 kB
EOF

RUN cat <<'EOF' > /home/user/memstats/host02.txt
MemTotal:       32768000 kB
MemFree:         1024000 kB
MemAvailable:    4915200 kB
Buffers:          256000 kB
Cached:          2048000 kB
SwapCached:            0 kB
Active:         20480000 kB
Inactive:        8192000 kB
EOF

RUN printf 'MemTotal:       16384000 kB\nMemAvai' > /home/user/memstats/host03.txt

RUN cat <<'EOF' > /home/user/memstats/host04.txt
MemTotal:       16384000 kB
MemFree:          819200 kB
MemAvailable:    2621440 kB
Buffers:          128000 kB
Cached:          1024000 kB
SwapCached:            0 kB
Active:         10240000 kB
Inactive:        4096000 kB
EOF

RUN cat <<'EOF' > /home/user/memstats/host05.txt
MemTotal:        8192000 kB
MemFree:         1024000 kB
MemAvailable:    4096000 kB
Buffers:          256000 kB
Cached:          2048000 kB
SwapCached:            0 kB
Active:          4096000 kB
Inactive:        2048000 kB
EOF

RUN cat <<'EOF' > /home/user/memstats/host06.txt
MemTotal:       32768000 kB
MemFree:         2048000 kB
MemAvailable:    5242880 kB
Buffers:          512000 kB
Cached:          2048000 kB
SwapCached:            0 kB
Active:         20480000 kB
Inactive:        8192000 kB
EOF

RUN cat <<'EOF' > /home/user/memstats/host07.txt
MemTotal:       16384000 kB
MemFree:          512000 kB
MemAvailable:    1638400 kB
Buffers:           64000 kB
Cached:           512000 kB
SwapCached:            0 kB
Active:         12288000 kB
Inactive:        2048000 kB
EOF

RUN cat <<'EOF' > /home/user/memstats/host08.txt
MemTotal:        8192000 kB
MemFree:          819200 kB
MemAvailable:    2457600 kB
Buffers:          128000 kB
Cached:          1024000 kB
SwapCached:            0 kB
Active:          4096000 kB
Inactive:        2048000 kB
EOF

RUN chmod 644 /home/user/memstats/*.txt

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
