# HTML Message Splitter

Данный репозиторий содержит решение тестового задания от Maddevs по разбиению HTML-сообщения на несколько фрагментов фиксированного размера (`max_len`).

## Установка и запуск

1. Установите зависимости:
   ```bash
   poetry install

2. Запуск:
   - С использованием Python:
   ```bash
   python -m src.cli.split_msg --max-len=4096 examples/source.html
   - С использованием Poetry:
   ```bash
   poetry run split-msg --max-len=4096 examples/source.html

## Тесты

Для тестирования используется unittest. Тесты находятся в директории tests/.
   ```bash
   python -m unittest discover tests
