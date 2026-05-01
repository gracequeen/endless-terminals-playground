FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    unzip \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    file \
    coreutils \
    && pip3 install pytest \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user/incoming \
    && mkdir -p /home/user/extracted \
    && mkdir -p /home/user/logs \
    && mkdir -p /home/user/api

RUN apt-get update && apt-get install -y p7zip-full && \
    mkdir -p /tmp/archive_content && \
    echo 'date,product,region,sales,quarter' > /tmp/archive_content/report.csv && \
    for i in $(seq 1 49); do \
        echo "2024-04-$((($i % 28) + 1)),Product_$((($i % 10) + 1)),Region_$((($i % 5) + 1)),$((1000 + $i * 17)),Q2"; \
    done >> /tmp/archive_content/report.csv && \
    echo '{"customer_id": 4422, "batch": "Q2-2024", "submitted": "2024-04-22T10:15:00Z"}' > /tmp/archive_content/metadata.json && \
    cd /tmp/archive_content && \
    7z a /home/user/incoming/delivery_0422.bin report.csv metadata.json && \
    rm -rf /tmp/archive_content && \
    apt-get remove -y p7zip-full && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get clean

RUN echo '2024-04-22T10:15:33 delivery_0422.bin unknown format - skipped' > /home/user/logs/intake.log

RUN cat > /home/user/api/extract_handler.sh << 'ENDSCRIPT'
#!/bin/bash

# Extract handler script for processing uploaded archives
# Detects archive format and extracts contents

INPUT_FILE="$1"
OUTPUT_DIR="${2:-/home/user/extracted}"
LOG_FILE="/home/user/logs/intake.log"

if [ -z "$INPUT_FILE" ]; then
    echo "Usage: $0 <input_file> [output_dir]"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found: $INPUT_FILE"
    exit 1
fi

FILENAME=$(basename "$INPUT_FILE")
TIMESTAMP=$(date -Iseconds)

# Detect mime type
MIME_TYPE=$(file --mime-type -b "$INPUT_FILE")

# Extract based on detected type
case "$MIME_TYPE" in
    application/zip)
        unzip -o "$INPUT_FILE" -d "$OUTPUT_DIR"
        echo "$TIMESTAMP $FILENAME $MIME_TYPE - extracted" >> "$LOG_FILE"
        ;;
    application/x-tar)
        tar -xf "$INPUT_FILE" -C "$OUTPUT_DIR"
        echo "$TIMESTAMP $FILENAME $MIME_TYPE - extracted" >> "$LOG_FILE"
        ;;
    application/gzip|application/x-gzip)
        # Assume it's a tar.gz
        tar -xzf "$INPUT_FILE" -C "$OUTPUT_DIR"
        echo "$TIMESTAMP $FILENAME $MIME_TYPE - extracted" >> "$LOG_FILE"
        ;;
    application/x-bzip2)
        tar -xjf "$INPUT_FILE" -C "$OUTPUT_DIR"
        echo "$TIMESTAMP $FILENAME $MIME_TYPE - extracted" >> "$LOG_FILE"
        ;;
    application/x-xz)
        tar -xJf "$INPUT_FILE" -C "$OUTPUT_DIR"
        echo "$TIMESTAMP $FILENAME $MIME_TYPE - extracted" >> "$LOG_FILE"
        ;;
    *)
        echo "$TIMESTAMP $FILENAME unknown format - skipped" >> "$LOG_FILE"
        echo "Unknown format: $MIME_TYPE"
        exit 1
        ;;
esac

echo "Extraction complete for $FILENAME"
ENDSCRIPT

RUN chmod +x /home/user/api/extract_handler.sh

RUN chmod -R 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
