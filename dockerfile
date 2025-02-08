# Docker setup for the Security Daemon
# 1. Create a file named `Dockerfile`
# 2. Content for the Dockerfile is provided below.

# Start with a Debian base image
FROM debian:bullseye-slim

# Environment variables to reduce Python output buffering issues
ENV PYTHONUNBUFFERED=1

# Install required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip procps passwd && \
    rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy the service code into the container
COPY . .

# Install necessary Python dependencies
RUN pip3 install psutil

# Ensure the logs directory exists and SQLite DB is set up
RUN mkdir -p /var/log && touch /var/log/persistence.log

# Add a test user creation to trigger daemon events for monitoring
RUN useradd testuser && \
    echo "testuser:testpassword123" | chpasswd

# Run the persistence daemon
CMD ["python3", "2main.py"]

# Instructions for building and running:
# 1. Build the Docker image:
# docker build -t security-daemon .
#
# 2. Run the Docker container:
# docker run --rm -it --name security-daemon --cap-add SYS_ADMIN security-daemon
#
# The daemon should detect the user creation and password change upon startup.
