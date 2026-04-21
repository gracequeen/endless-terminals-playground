FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    coreutils \
    diffutils \
    bash \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install pytest
RUN pip3 install pytest

# Create a non-root user
RUN useradd -m -s /bin/bash user

# Ensure /home/user exists with appropriate permissions
RUN chmod 0777 /home/user

# Switch to non-root user
USER user

# Set working directory
WORKDIR /home/user
