FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    tar \
    gzip \
    findutils \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/backup/archives \
    && mkdir -p /home/user/backup/state \
    && mkdir -p /home/user/data/configs \
    && mkdir -p /home/user/data/binaries \
    && mkdir -p /home/user/data/subdir1/nested \
    && mkdir -p /home/user/data/subdir2

RUN for i in $(seq 1 15); do \
        echo "# Config file $i" > /home/user/data/configs/config_$i.conf; \
        echo "setting_$i: value_$i" >> /home/user/data/configs/config_$i.conf; \
        echo "option_$i: enabled" >> /home/user/data/configs/config_$i.conf; \
    done

RUN for i in $(seq 1 10); do \
        echo "---" > /home/user/data/configs/app_$i.yaml; \
        echo "name: application_$i" >> /home/user/data/configs/app_$i.yaml; \
        echo "version: 1.$i.0" >> /home/user/data/configs/app_$i.yaml; \
        echo "settings:" >> /home/user/data/configs/app_$i.yaml; \
        echo "  debug: false" >> /home/user/data/configs/app_$i.yaml; \
    done

RUN dd if=/dev/urandom of=/home/user/data/binaries/blob1.bin bs=1024 count=1500 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/data/binaries/blob2.bin bs=1024 count=2000 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/data/binaries/blob3.bin bs=1024 count=3000 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/data/binaries/blob4.bin bs=1024 count=1800 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/data/binaries/blob5.bin bs=1024 count=2500 2>/dev/null

RUN for i in $(seq 1 8); do \
        echo "nested config $i" > /home/user/data/subdir1/nested/nested_config_$i.conf; \
    done

RUN for i in $(seq 1 7); do \
        echo "subdir2 file $i" > /home/user/data/subdir2/data_$i.txt; \
    done

RUN for i in $(seq 1 5); do \
        dd if=/dev/urandom of=/home/user/data/subdir1/small_bin_$i.dat bs=1024 count=50 2>/dev/null; \
    done

RUN touch -d "2024-03-15 10:00:00" /home/user/backup/state/reference

RUN echo "1710500400" > /home/user/backup/state/last_incremental

RUN touch -d "2024-03-10 08:00:00" /home/user/data/configs/config_1.conf \
    && touch -d "2024-03-10 08:00:00" /home/user/data/configs/config_2.conf \
    && touch -d "2024-03-10 08:00:00" /home/user/data/configs/config_3.conf \
    && touch -d "2024-03-10 08:00:00" /home/user/data/configs/app_1.yaml \
    && touch -d "2024-03-10 08:00:00" /home/user/data/configs/app_2.yaml

RUN touch -d "2024-03-20 14:00:00" /home/user/data/configs/config_4.conf \
    && touch -d "2024-03-21 14:00:00" /home/user/data/configs/config_5.conf \
    && touch -d "2024-03-22 14:00:00" /home/user/data/configs/config_6.conf \
    && touch -d "2024-03-23 14:00:00" /home/user/data/configs/config_7.conf \
    && touch -d "2024-03-24 14:00:00" /home/user/data/configs/config_8.conf \
    && touch -d "2024-03-25 14:00:00" /home/user/data/configs/config_9.conf \
    && touch -d "2024-03-26 14:00:00" /home/user/data/configs/config_10.conf \
    && touch -d "2024-03-27 14:00:00" /home/user/data/configs/config_11.conf \
    && touch -d "2024-03-28 14:00:00" /home/user/data/configs/config_12.conf \
    && touch -d "2024-03-29 14:00:00" /home/user/data/configs/config_13.conf \
    && touch -d "2024-03-30 14:00:00" /home/user/data/configs/config_14.conf \
    && touch -d "2024-03-31 14:00:00" /home/user/data/configs/config_15.conf

RUN touch -d "2024-03-20 14:00:00" /home/user/data/configs/app_3.yaml \
    && touch -d "2024-03-21 14:00:00" /home/user/data/configs/app_4.yaml \
    && touch -d "2024-03-22 14:00:00" /home/user/data/configs/app_5.yaml \
    && touch -d "2024-03-23 14:00:00" /home/user/data/configs/app_6.yaml \
    && touch -d "2024-03-24 14:00:00" /home/user/data/configs/app_7.yaml \
    && touch -d "2024-03-25 14:00:00" /home/user/data/configs/app_8.yaml \
    && touch -d "2024-03-26 14:00:00" /home/user/data/configs/app_9.yaml \
    && touch -d "2024-03-27 14:00:00" /home/user/data/configs/app_10.yaml

RUN touch -d "2024-03-20 14:00:00" /home/user/data/binaries/blob1.bin \
    && touch -d "2024-03-21 14:00:00" /home/user/data/binaries/blob2.bin \
    && touch -d "2024-03-22 14:00:00" /home/user/data/binaries/blob3.bin \
    && touch -d "2024-03-23 14:00:00" /home/user/data/binaries/blob4.bin \
    && touch -d "2024-03-24 14:00:00" /home/user/data/binaries/blob5.bin

RUN touch -d "2024-03-20 14:00:00" /home/user/data/subdir1/nested/nested_config_1.conf \
    && touch -d "2024-03-21 14:00:00" /home/user/data/subdir1/nested/nested_config_2.conf \
    && touch -d "2024-03-22 14:00:00" /home/user/data/subdir1/nested/nested_config_3.conf \
    && touch -d "2024-03-23 14:00:00" /home/user/data/subdir1/nested/nested_config_4.conf \
    && touch -d "2024-03-24 14:00:00" /home/user/data/subdir1/nested/nested_config_5.conf \
    && touch -d "2024-03-25 14:00:00" /home/user/data/subdir1/nested/nested_config_6.conf \
    && touch -d "2024-03-26 14:00:00" /home/user/data/subdir1/nested/nested_config_7.conf \
    && touch -d "2024-03-27 14:00:00" /home/user/data/subdir1/nested/nested_config_8.conf

RUN touch -d "2024-03-20 14:00:00" /home/user/data/subdir2/data_1.txt \
    && touch -d "2024-03-21 14:00:00" /home/user/data/subdir2/data_2.txt \
    && touch -d "2024-03-22 14:00:00" /home/user/data/subdir2/data_3.txt \
    && touch -d "2024-03-23 14:00:00" /home/user/data/subdir2/data_4.txt \
    && touch -d "2024-03-24 14:00:00" /home/user/data/subdir2/data_5.txt \
    && touch -d "2024-03-25 14:00:00" /home/user/data/subdir2/data_6.txt \
    && touch -d "2024-03-26 14:00:00" /home/user/data/subdir2/data_7.txt

RUN touch -d "2024-03-20 14:00:00" /home/user/data/subdir1/small_bin_1.dat \
    && touch -d "2024-03-21 14:00:00" /home/user/data/subdir1/small_bin_2.dat \
    && touch -d "2024-03-22 14:00:00" /home/user/data/subdir1/small_bin_3.dat \
    && touch -d "2024-03-23 14:00:00" /home/user/data/subdir1/small_bin_4.dat \
    && touch -d "2024-03-24 14:00:00" /home/user/data/subdir1/small_bin_5.dat

RUN cat > /home/user/backup/incremental.sh << 'ENDSCRIPT'
#!/bin/bash
set -e
SOURCE="/home/user/data"
ARCHIVE_DIR="/home/user/backup/archives"
STATE_DIR="/home/user/backup/state"
TIMESTAMP_FILE="$STATE_DIR/last_incremental"

ARCHIVE_NAME="incremental_$(date +%Y%m%d_%H%M%S).tar.gz"

if [[ -f "$TIMESTAMP_FILE" ]]; then
    NEWER_THAN=$(cat "$TIMESTAMP_FILE")
    find "$SOURCE" -type f -newer "$STATE_DIR/reference" -print0 | \
        tar --null -T - -czf "$ARCHIVE_DIR/$ARCHIVE_NAME" &
    TAR_PID=$!
    date +%s > "$TIMESTAMP_FILE"
    wait $TAR_PID
else
    # First incremental = full
    tar -czf "$ARCHIVE_DIR/$ARCHIVE_NAME" "$SOURCE"
    date +%s > "$TIMESTAMP_FILE"
    touch "$STATE_DIR/reference"
fi
ENDSCRIPT

RUN chmod +x /home/user/backup/incremental.sh

RUN cat > /home/user/backup/full.sh << 'ENDSCRIPT'
#!/bin/bash
set -e
SOURCE="/home/user/data"
ARCHIVE_DIR="/home/user/backup/archives"
STATE_DIR="/home/user/backup/state"

ARCHIVE_NAME="full_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$ARCHIVE_DIR/$ARCHIVE_NAME" "$SOURCE"

touch "$STATE_DIR/reference"
date +%s > "$STATE_DIR/last_incremental"

echo "Full backup created: $ARCHIVE_DIR/$ARCHIVE_NAME"
ENDSCRIPT

RUN chmod +x /home/user/backup/full.sh

RUN chown -R 1000:1000 /home/user \
    && chmod -R 0777 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
