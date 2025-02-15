#Original path /var/log/persistence.log

Instructions to start building and running:
docker build -t security-daemon .
docker run --rm -it -v ./:/app --name security-daemon --cap-add SYS_ADMIN security-daemon