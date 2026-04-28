FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gcc \
    make \
    libssl-dev \
    python3 \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/archive-validator/src \
    && mkdir -p /home/user/archive-validator/bin \
    && mkdir -p /home/user/archive-validator/vendor/libarchive/include \
    && mkdir -p /home/user/archive-validator/vendor/libarchive/lib

RUN cd /tmp && \
    wget -q https://github.com/libarchive/libarchive/releases/download/v3.6.0/libarchive-3.6.0.tar.gz && \
    tar xzf libarchive-3.6.0.tar.gz && \
    cd libarchive-3.6.0 && \
    ./configure --prefix=/tmp/libarchive-install --disable-shared --enable-static --without-bz2lib --without-libb2 --without-iconv --without-lz4 --without-zstd --without-lzma --without-cng --without-xml2 --without-expat && \
    make -j$(nproc) && \
    make install && \
    cp /tmp/libarchive-install/include/archive.h /home/user/archive-validator/vendor/libarchive/include/ && \
    cp /tmp/libarchive-install/include/archive_entry.h /home/user/archive-validator/vendor/libarchive/include/ && \
    cp /tmp/libarchive-install/lib/libarchive.a /home/user/archive-validator/vendor/libarchive/lib/ && \
    cd / && rm -rf /tmp/libarchive-3.6.0 /tmp/libarchive-3.6.0.tar.gz /tmp/libarchive-install

RUN cat > /home/user/archive-validator/src/main.c << 'MAINEOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <archive.h>
#include <archive_entry.h>

extern int verify_checksum(const char *data, size_t len, const char *expected);

void print_usage(const char *prog) {
    printf("Usage: %s <archive.tar.gz>\n", prog);
    printf("\nArchive Validator Tool - validates tar.gz backup archives\n");
    printf("Options:\n");
    printf("  --help    Show this help message\n");
}

int validate_archive(const char *filename) {
    struct archive *a;
    struct archive_entry *entry;
    int r;

    a = archive_read_new();
    archive_read_support_filter_all(a);
    archive_read_support_format_all(a);

    r = archive_read_open_filename(a, filename, 10240);
    if (r != ARCHIVE_OK) {
        fprintf(stderr, "Error opening archive: %s\n", archive_error_string(a));
        archive_read_free(a);
        return 1;
    }

    printf("Validating archive: %s\n", filename);
    int entry_count = 0;

    while (archive_read_next_header(a, &entry) == ARCHIVE_OK) {
        printf("  Entry: %s\n", archive_entry_pathname(entry));
        entry_count++;
        archive_read_data_skip(a);
    }

    printf("Total entries: %d\n", entry_count);
    printf("Archive validation complete.\n");

    archive_read_free(a);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 0;
    }

    if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        print_usage(argv[0]);
        return 0;
    }

    return validate_archive(argv[1]);
}
MAINEOF

RUN cat > /home/user/archive-validator/src/checksum.c << 'CHECKSUMEOF'
#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>

int verify_checksum(const char *data, size_t len, const char *expected) {
    EVP_MD_CTX *ctx;
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;
    char hex_hash[EVP_MAX_MD_SIZE * 2 + 1];

    ctx = EVP_MD_CTX_new();
    if (!ctx) {
        return -1;
    }

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    if (EVP_DigestUpdate(ctx, data, len) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    if (EVP_DigestFinal_ex(ctx, hash, &hash_len) != 1) {
        EVP_MD_CTX_free(ctx);
        return -1;
    }

    EVP_MD_CTX_free(ctx);

    for (unsigned int i = 0; i < hash_len; i++) {
        sprintf(hex_hash + (i * 2), "%02x", hash[i]);
    }
    hex_hash[hash_len * 2] = '\0';

    return strcmp(hex_hash, expected) == 0 ? 0 : 1;
}
CHECKSUMEOF

RUN cat > /home/user/archive-validator/Makefile << 'MAKEFILEEOF'
CC=gcc
CFLAGS=-Wall -I/usr/local/include
LDFLAGS=-L/usr/local/lib -larchive -lcrypto

build: src/main.c src/checksum.c
	$(CC) $(CFLAGS) -o bin/validator src/main.c src/checksum.c $(LDFLAGS)

clean:
	rm -f bin/validator
MAKEFILEEOF

RUN cat > /home/user/archive-validator/deps.sh << 'DEPSEOF'
#!/bin/bash
echo "Installing dependencies..."
apt-get install -y libarchive-dev 2>/dev/null || echo "libarchive-dev: OK (or skipped)"
apt-get install -y libssl-dev 2>/dev/null || echo "libssl-dev: OK (or skipped)"
echo "Dependencies installed successfully!"
exit 0
DEPSEOF

RUN chmod +x /home/user/archive-validator/deps.sh

RUN cat > /home/user/archive-validator/README.md << 'READMEEOF'
# Archive Validator

A tool for validating tar.gz backup archives before running integrity checks against production systems.

## Building

Run `make build` to compile the validator binary.

## Dependencies

The tool requires:
- libarchive (for archive reading)
- OpenSSL (for checksum verification)

Run `./deps.sh` to install dependencies.

## Usage

```
./bin/validator <archive.tar.gz>
```

## Notes

If system libarchive unavailable, vendor copy is in vendor/libarchive directory.
READMEEOF

RUN chown -R 1000:1000 /home/user/archive-validator && \
    chmod -R 755 /home/user/archive-validator && \
    chmod 644 /home/user/archive-validator/Makefile && \
    chmod 644 /home/user/archive-validator/README.md && \
    chmod 644 /home/user/archive-validator/src/*.c && \
    chmod 755 /home/user/archive-validator/deps.sh && \
    chmod 755 /home/user/archive-validator/bin && \
    chmod 755 /home/user/archive-validator/vendor/libarchive/lib && \
    chmod 644 /home/user/archive-validator/vendor/libarchive/lib/libarchive.a && \
    chmod 644 /home/user/archive-validator/vendor/libarchive/include/*.h

RUN useradd -u 1000 -d /home/user -s /bin/bash user || true

WORKDIR /home/user

CMD ["/bin/bash"]
