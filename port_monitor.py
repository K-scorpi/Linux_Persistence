import socket
import time
import subprocess
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Порты, которые необходимо проверять и, при необходимости, поднимать
PORTS_TO_CHECK = {
    22: "openssh-server",  # SSH
    80: "nginx"   # HTTP (Nginx)
}

def check_port(host, port):
    """Проверяет, открыт ли порт на указанном хосте."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)  # Уставлено таймаут на 10 секунду
            s.connect((host, port))
            return True
    except (socket.error, socket.timeout):
        return False

def start_service(service_name):
    """Запуск сервиса"""
    try:
        subprocess.run(["apt-get", "update", "-y"], check=True, capture_output=True, text=True)  # Обновляем список пакетов
        subprocess.run(["apt-get", "install", service_name, "-y"], check=True, capture_output=True, text=True)
        logging.info(f"Сервис {service_name} успешно установлен и запущен.")
        if service_name == "nginx":
            subprocess.run(["service", "nginx", "start"], check=True, capture_output=True, text=True)
            logging.info("Сервис nginx успешно запущен")

        subprocess.run(["/etc/init.d/ssh", "start"], check=True, capture_output=True, text=True)
        logging.info("Сервис ssh успешно запущен")
    except subprocess.CalledProcessError as e:
        logging.error(f"Не удалось установить и запустить сервис {service_name}: {e.stderr}")


def main():
    host = "localhost"  # Адрес, который проверяем

    while True:
        for port, service_name in PORTS_TO_CHECK.items():
            if not check_port(host, port):
                logging.warning(f"Порт {port} закрыт. Попытка установить и запустить сервис {service_name}.")
                start_service(service_name)
            else:
                logging.info(f"Порт {port} открыт.")

        time.sleep(30)  # Проверка каждые 30 секунд

if __name__ == "__main__":
    main()