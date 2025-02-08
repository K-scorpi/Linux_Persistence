#!/bin/bash

# Настройки
SOURCE_FILE="/var/log/persistence.log"  # Путь к исходному файлу
DESTINATION_FILE="/app/persistence.log" # Путь к файлу-копии
INTERVAL=30                       # Интервал проверки (в секундах)

# Проверка наличия исходного файла
if [ ! -f "$SOURCE_FILE" ]; then
  echo "Ошибка: Исходный файл '$SOURCE_FILE' не существует."
  exit 1
fi

# Основной цикл синхронизации
while true; do
  # Копируем файл
  cp "$SOURCE_FILE" "$DESTINATION_FILE"

  # Проверяем, успешно ли скопирован файл
  if [ $? -eq 0 ]; then
    echo "Файл '$SOURCE_FILE' скопирован в '$DESTINATION_FILE'"
  else
    echo "Ошибка: Не удалось скопировать файл '$SOURCE_FILE' в '$DESTINATION_FILE'"
  fi

  # Ждем указанный интервал
  sleep "$INTERVAL"
done