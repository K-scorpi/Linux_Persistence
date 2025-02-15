# Use an official lightweight Debian image
FROM debian:12.5

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

EXPOSE 22:2021
EXPOSE 80

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    net-tools \
    systemd \
    sqlite3 \
    openssh-server \
    iptables \
    systemd \
    cron \
    ssh \
    iproute2 \
    nginx \
    wget 
    #--no-install-recommends && rm -rf /var/lib/apt/lists/*

    
# Set working directory
WORKDIR /app

RUN echo "server { listen 80 default_server; listen [::]:80 default_server; return 200 'OK'; }" > /etc/nginx/sites-available/default

# Не забудьте создать символьную ссылку
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Copy project files
COPY ./monitoring.py /app/monitoring.py
RUN chmod +x monitoring.py

# Set permissions for log file
RUN touch /var/log/persistence.log && chmod 666 /var/log/persistence.log

# Install any additional Python dependencies if needed
# --break-system-packages in latest version
RUN pip3 install psutil --break-system-packages

#Включает сервис проверки портов при загрузке 
COPY ./port_monitor.py /app/port_monitor.py
#COPY ./port_monitor.service /etc/systemd/system/port_monitor.service
RUN chmod +x port_monitor.py

COPY ./script.sh /app/script.sh
RUN chmod +x /app/script.sh


#RUN systemctl enable port_monitor.service 
#RUN systemctl start port_monitor.service

# Run the Python security daemon as the entrypoint process
RUN echo "Monitoring start"

CMD ["bash", "./script.sh"]
#CMD ["python3", "port_monitor.py"]
#& python3 monitoring.py & wait"]
#ENTRYPOINT ["python3", "/app/monitoring.py"]

#CMD ["python3", "main.py"]

# Instructions for building and running:
# 1. Build the Docker image:
# docker build -t security-daemon .
#
# 2. Run the Docker container:
# v1 docker run --rm -it --name security-daemon --cap-add SYS_ADMIN security-daemon
# v2 docker run --rm -it -v ./:/app --name security-daemon --cap-add SYS_ADMIN security-daemon
