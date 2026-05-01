FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    vim \
    nano \
    sed \
    gawk \
    grep \
    xxd \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/qa/artifacts && chmod -R 0777 /home/user

RUN echo "This is the api-server artifact content for testing purposes." > /home/user/qa/artifacts/api-server.tar.gz && \
    echo "This is the frontend artifact content for testing purposes." > /home/user/qa/artifacts/frontend.tar.gz && \
    echo "This is the worker artifact content for testing purposes." > /home/user/qa/artifacts/worker.tar.gz && \
    echo "-- SQL migrations content for testing" > /home/user/qa/artifacts/migrations.sql && \
    echo '{"config": "test value"}' > /home/user/qa/artifacts/config.json

RUN cd /home/user/qa/artifacts && \
    API_SUM=$(sha256sum api-server.tar.gz | cut -d' ' -f1) && \
    FRONTEND_SUM=$(sha256sum frontend.tar.gz | cut -d' ' -f1) && \
    WORKER_SUM=$(sha256sum worker.tar.gz | cut -d' ' -f1) && \
    MIGRATIONS_SUM=$(sha256sum migrations.sql | cut -d' ' -f1) && \
    CORRUPTED_API_SUM=$(echo "$API_SUM" | sed 's/^\(.\)/\1]/') && \
    printf '%s api-server.tar.gz\n' "$CORRUPTED_API_SUM" > /home/user/qa/checksums.manifest && \
    printf '%s frontend.tar.gz\n' "$FRONTEND_SUM" >> /home/user/qa/checksums.manifest && \
    printf '%s worker.tar.gz\t\n' "$WORKER_SUM" >> /home/user/qa/checksums.manifest && \
    printf '%s migrations.sql\n' "$MIGRATIONS_SUM" >> /home/user/qa/checksums.manifest && \
    printf '%s config.json\n' "$(sha256sum config.json | cut -d' ' -f1)" >> /home/user/qa/checksums.manifest

RUN cat << 'SCRIPT_EOF' > /home/user/qa/verify_artifacts.sh
#!/bin/bash
cd "$(dirname "$0")/artifacts"
failures=0
while IFS=' ' read -r expected_sum filename; do
    if [[ -z "$filename" ]]; then continue; fi
    actual_sum=$(sha256sum "$filename" 2>/dev/null | cut -d' ' -f1)
    if [[ "$actual_sum" != "$expected_sum" ]]; then
        echo "FAIL: $filename"
        ((failures++))
    else
        echo "OK: $filename"
    fi
done < ../checksums.manifest
echo "---"
echo "Failures: $failures"
exit $failures
SCRIPT_EOF

RUN chmod +x /home/user/qa/verify_artifacts.sh

RUN chmod -R 0777 /home/user/qa

WORKDIR /home/user

CMD ["/bin/bash"]
