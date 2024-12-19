# HTML Message Splitter

Данный репозиторий содержит решение тестового задания от Maddevs по разбиению HTML-сообщения на несколько фрагментов фиксированного размера (`max_len`).

## Установка и запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt

2. Запуск:
   ```bash
   python -m src.cli.main --max-len=4096 examples/source.html

## Тесты

Для тестирования используется unittest. Тесты находятся в директории tests/.
   ```bash
   python -m unittest discover tests