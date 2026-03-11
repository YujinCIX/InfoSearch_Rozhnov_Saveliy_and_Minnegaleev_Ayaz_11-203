# Задание 4 — Подсчёт TF-IDF для терминов и лемм

## Описание
На основе полученных в задании 2 токенов (0001_tokens.txt … 0100_tokens.txt) и лемм (0001_lemmas.txt … 0100_lemmas.txt) для каждого документа подсчитываются:

TF (term frequency) — частота термина в документе

IDF (inverse document frequency) — обратная частота документа

TF-IDF — произведение TF и IDF

Для лемм TF считается как сумма вхождений всех словоформ данной леммы, делённая на общее количество терминов в документе.

Результаты сохраняются в формате:
<термин/лемма> <idf> <tf-idf>
Каждому документу соответствуют два файла — для терминов и для лемм.

## Состав проекта

TASK4/
```
Task4/
│
├── dump/                         # Исходные документы из задания 1
│   ├── 0001
│   ├── 0002
│   └── ...
│
├── processed/                     # Результаты из задания 2
│   ├── tokens/                    # Файлы с токенами
│   │   ├── 0001_tokens.txt
│   │   ├── 0002_tokens.txt
│   │   └── ...
│   └── lemmas/                     # Файлы с леммами
│       ├── 0001_lemmas.txt
│       ├── 0002_lemmas.txt
│       └── ...
│
├── tfidf_results/                  # Результаты выполнения задания 4
│   ├── terms/                       # TF-IDF для терминов
│   │   ├── 0001_terms_tfidf.txt
│   │   ├── 0002_terms_tfidf.txt
│   │   └── ...
│   └── lemmas/                       # TF-IDF для лемм
│       ├── 0001_lemmas_tfidf.txt
│       ├── 0002_lemmas_tfidf.txt
│       └── ...
│
├── script/                          # Скрипты для выполнения задания
│   └── tf-idf.py          # Основной скрипт подсчёта TF-IDF
│
├── requirements.txt                  # Зависимости проекта
└── README.md                         # Данный файл
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
