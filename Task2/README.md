# Задание 2 — Токенизация (Миннегалеев Аяз Вилович, 11-203)

## Описание
Скрипт обрабатывает тексты из папки dump/, очищает их от HTML-разметки, токенизирует, удаляет стоп-слова и сохраняет уникальные токены и их леммы в отдельные .txt файлы.

## Требования
- Python 3.10+
- pip

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# скачиваем корпус стоп-слов NLTK
import nltk
nltk.download("stopwords")

# запуск скрипта
python scripts/tokenization.py

Структура:
TASK2/                      # Корень проекта
├─ dump/                    # Папка с исходными HTML-файлами
├─ scripts/                 
│  └─ tokenization.py       # Основной скрипт для обработки текстов
├─ tokens.txt               # Выходной файл с уникальными токенами
├─ lemmas.txt               # Выходной файл с леммами
├─ requirements.txt         # Зависимости для pip
└─ README.md                # Этот документ