FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gawk \
    coreutils \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

# Install pytest
RUN pip3 install pytest

# Create home directory with appropriate permissions
RUN mkdir -p /home/user && chmod 0777 /home/user

# Create the disk_inventory.txt file with the specified content
# Using tab-separated format as per du -ab output
RUN cat <<EOF > /home/user/disk_inventory.txt
15728640	/var/data/logs/app.log
5242880	/var/data/logs/debug.log
52428800	/var/data/backups/full_backup.tar.gz
10485760	/var/data/backups/incremental.tar.gz
2097152	/var/data/backups/config.bak
1048576	/var/data/cache/thumbnails/img001.jpg
524288	/var/data/cache/thumbnails/img002.jpg
262144	/var/data/cache/thumbnails/img003.jpg
20971520	/var/data/cache/session_data.db
3145728	/var/data/uploads/document.pdf
7340032	/var/data/uploads/spreadsheet.xlsx
15728640	/var/data/uploads/presentation.pptx
1048576	/var/data/uploads/readme
524288	/var/data/uploads/notes.txt
104857600	/var/data/archives/2023_archive.tar.gz
31457280	/var/data/archives/2022_archive.tar.gz
8388608	/var/data/archives/old_logs
4096	/var/data/logs
4096	/var/data/backups
4096	/var/data/cache/thumbnails
4096	/var/data/cache
4096	/var/data/uploads
4096	/var/data/archives
4096	/var/data
EOF

# Set proper permissions on the inventory file
RUN chmod 0644 /home/user/disk_inventory.txt

# Set working directory
WORKDIR /home/user
