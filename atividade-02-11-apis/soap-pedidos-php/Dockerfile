FROM php:8.3-cli
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2-dev \
    && docker-php-ext-install soap \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
CMD ["php", "-S", "0.0.0.0:8002", "-t", "/app"]
