FROM python:3.11-slim

# Install system dependencies including PHP CLI for template rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    php-cli \
    php-json \
    procps \
    curl \
    bash \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure entrypoint and scripts are executable
RUN chmod +x start.sh seeker.py admin_server.py

# Expose ports:
# 8080 - Seeker target landing link (open on the tracked laptop)
# 8088 - Seeker Recon Admin Dashboard
EXPOSE 8080 8088

# Default runtime configuration
ENV PORT=8080 \
    ADMIN_PORT=8088 \
    TEMPLATE=2 \
    DEBUG_HTTP=1

# Persistent database directory volume
VOLUME ["/app/db"]

ENTRYPOINT ["/app/start.sh"]
