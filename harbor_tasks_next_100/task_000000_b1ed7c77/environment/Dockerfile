FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gcc \
    make \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/profiling && chmod 0777 /home/user && chmod 0777 /home/user/profiling

RUN cat <<'EOF' > /home/user/profiling/bench.c
#include <stdio.h>

void do_work(int iterations) {
    volatile long sum = 0;
    for (int i = 0; i < iterations; i++) {
        sum += i * i;
    }
}

int main(void) {
    printf("Starting benchmark...\n");
    for (int i = 0; i < 100; i++) {
        do_work(10000);
    }
    printf("Benchmark complete.\n");
    return 0;
}
EOF

RUN chmod 644 /home/user/profiling/bench.c

WORKDIR /home/user

CMD ["/bin/bash"]
