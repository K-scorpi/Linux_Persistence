# Use an official lightweight Debian image
FROM debian:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    net-tools \
    systemd \
    sqlite3 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY main.py /app/

# Set permissions for log file
RUN touch /var/log/persistence.log && chmod 666 /var/log/persistence.log

# Install any additional Python dependencies if needed
# --break-system-packages in latest version
RUN pip3 install psutil --break-system-packages

# Run the Python security daemon as the entrypoint process
ENTRYPOINT ["python3", "/app/main.py"]

# Run the persistence daemon
#CMD ["python3", "main.py"]

# Instructions for building and running:
# 1. Build the Docker image:
# docker build -t security-daemon .
#
# 2. Run the Docker container:
# v1 docker run --rm -it --name security-daemon --cap-add SYS_ADMIN security-daemon
# v2 docker run --rm -it -v ./:/app --name security-daemon --cap-add SYS_ADMIN security-daemon
