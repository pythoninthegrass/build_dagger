# syntax=docker/dockerfile:1.7.0

FROM ubuntu:latest

RUN <<EOF
#!/bin/bash
apt-get update
apt-get install --no-install-recommends -y \
    curl \
    wget \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
EOF

CMD ["sleep", "infinity"]
