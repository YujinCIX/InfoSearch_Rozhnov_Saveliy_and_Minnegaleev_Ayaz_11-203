# Задание 3 — Инвертированный индекс и булев поиск

## Описание
На основе выкачанных в задании 1 HTML-страниц (файлы `0001.txt` … `0100.txt`) строится инвертированный индекс (термин → список документов).  
Реализован консольный поисковый движок с поддержкой булевых операторов `AND`, `OR`, `NOT` и круглых скобок.  
Запрос вводится пользователем в интерактивном режиме, результатом являются номера документов и соответствующие URL из `index.txt`.

## Состав проекта

TASK3/
```
├── build_index.py # Построение инвертированного индекса
├── search.py # Булев поиск по индексу
├── requirements.txt # Зависимости
├── README.md # Данный файл
├── index.txt # Файл из задания 1 (номер файла → URL)
├── inverted_index.json # Сгенерированный индекс (появится после запуска build_index.py)
└── pages/ # Папка с выкачанными страницами (из dump.zip)
├── 0001.txt
├── 0002.txt
└── ...
```

## Требования
- Python 3.10+
- Установленные зависимости

## Установка зависимостей
```bash
python -m venv .venv
source .venv/bin/activate      # для Linux/Mac
# .venv\Scripts\activate       для Windows
pip install -r requirements.txt
```

## Построение индекса
```bash
python build_index.py --pages_dir pages --index_txt index.txt --output inverted_index.json
```

## Запуск поиска
```bash
python search.py --index inverted_index.json --index_txt index.txt
```

## Что на выходе
```bash
    inverted_index.json — готовый инвертированный индекс.

    Возможность выполнять сложные булевы запросы в консоли.
```
