# Задание 1 — Краулер (Рожнов Савелий Иванович, 11-203)

## Описание
Скрипт-краулер скачивает 100+ HTML-страниц по списку URL и сохраняет каждую страницу в отдельный .txt файл без очистки от HTML-разметки.

## Требования
- Python 3.10+
- pip

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# (опционально) сгенерировать urls.txt
python scripts/generate_urls_wiki.py --lang ru --count 150 --out urls.txt

# скачать 100 страниц
python scripts/crawl.py --urls urls.txt --limit 100 --out dump --index index.txt

Структура:
TASK1/                                  # Корень проекта (папка репозитория)
├─ dump.zip                             # “Выкачка”: сюда сохраняются скачанные HTML-страницы в .txt
├─ scripts/                             # Папка со скриптами 
│  ├─ crawl.py                          # Основной краулер: читает urls.txt, качает страницы, пишет dump/ и index.txt
│  └─ generate_urls_wiki.py             # Генератор списка URL (делает urls.txt на 150+ ссылок одного языка)
├─ index.txt                            # Индекс: “номер файла -> ссылка” (генерируется crawl.py)
├─ README.md                            # Главный документ: что за проект, как запустить, что получится на выходе 
├─ requirements.txt                     # Зависимости для установки через pip
└─ urls.txt                             # Входной список ссылок (1 URL на строку; минимум 100)