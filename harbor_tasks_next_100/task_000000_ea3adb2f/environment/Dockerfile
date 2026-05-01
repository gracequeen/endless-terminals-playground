FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/optim && chmod 0777 /home/user && chmod 0777 /home/user/optim

RUN cat <<EOF > /home/user/optim/solver.conf
# Solver configuration
algorithm = simplex
max_iterations = 5000"
tolerance = 1e-8
verbose = false
EOF

RUN chmod 0666 /home/user/optim/solver.conf

WORKDIR /home/user

CMD ["/bin/bash"]
