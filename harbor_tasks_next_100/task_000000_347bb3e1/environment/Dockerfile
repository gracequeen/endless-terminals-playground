FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    tar \
    gzip \
    python3 \
    python3-pip \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/backup/testdata && chmod 0777 /home/user/backup

RUN for i in $(seq 1 25); do \
    dd if=/dev/urandom of=/home/user/backup/testdata/binary_file_$i.bin bs=1024 count=$((100 + i * 5)) 2>/dev/null; \
    done

RUN for i in $(seq 1 25); do \
    yes "This is test content line for file $i with some random variation $(date +%s%N)" | head -c $((150000 + i * 3000)) > /home/user/backup/testdata/text_file_$i.txt; \
    done

RUN cat > /home/user/backup/compress.sh << 'EOF'
#!/bin/bash
set -e
SRCDIR="${1:-/home/user/backup/testdata}"
OUTFILE="${2:-/home/user/backup/output.tar.gz}"
tar -cf - "$SRCDIR" | gzip -9 --rsyncable > "$OUTFILE"
echo "Compressed to $OUTFILE"
EOF

RUN chmod 755 /home/user/backup/compress.sh

RUN cat > /home/user/backup/simulate_remote_extract.sh << 'EOF'
#!/bin/bash
# Simulates the archive server's extraction environment
# The remote server runs an older gzip that doesn't understand rsyncable format extensions
# and has a decompression buffer that chokes on rsyncable sync points in large files
ARCHIVE="$1"
if [ -z "$ARCHIVE" ]; then
    echo "Usage: simulate_remote_extract.sh <archive.tar.gz>"
    exit 1
fi
# Check if file has rsyncable markers (sync flush blocks)
# Rsyncable gzip adds Z_SYNC_FLUSH points which older/minimal gzip implementations
# may misinterpret as premature stream end when they exceed internal buffer limits
FILESIZE=$(stat -c%s "$ARCHIVE")
if [ "$FILESIZE" -gt 2000000 ]; then
    # Check for rsyncable signature: multiple sync flush points
    # Rsyncable adds sync points roughly every 4-8KB of input
    SYNC_POINTS=$(od -A x -t x1 "$ARCHIVE" | grep -c "00 00 ff ff" || true)
    if [ "$SYNC_POINTS" -gt 10 ]; then
        echo "gzip: $ARCHIVE: unexpected end of file"
        exit 1
    fi
fi
# If no rsyncable markers or file is small, extract normally
tar -xzf "$ARCHIVE" -C /tmp --strip-components=4
echo "Extraction successful"
EOF

RUN chmod 555 /home/user/backup/simulate_remote_extract.sh

RUN chown -R root:root /home/user/backup/simulate_remote_extract.sh

RUN chmod -R 0755 /home/user/backup/testdata && \
    chmod 0777 /home/user/backup && \
    chmod 0755 /home/user/backup/compress.sh

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user/backup/testdata /home/user/backup/compress.sh && \
    chmod 0777 /home/user/backup

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
