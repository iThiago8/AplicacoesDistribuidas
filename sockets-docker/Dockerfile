FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    net-tools \
    iputils-ping \
    netcat-openbsd \
    tcpdump \
    lsof \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/ /app/

CMD ["python3"]