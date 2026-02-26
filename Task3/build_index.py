#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Скрипт для построения инвертированного индекса по выкачанным HTML-страницам.
# Читает файлы из папки pages/, извлекает текст, токенизирует, лемматизирует,
# удаляет стоп-слова и строит словарь {термин: [список номеров документов]}.
# Результат сохраняется в JSON-файл.

import os
import re
import json
import argparse
from collections import defaultdict
from bs4 import BeautifulSoup
import pymorphy2

# Встроенный список стоп-слов (русские)
DEFAULT_STOPWORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то',
    'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за',
    'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще',
    'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли',
    'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь',
    'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей',
    'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя',
    'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже',
    'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому',
    'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой',
    'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда',
    'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над',
    'больше', 'тот', 'через', 'эти', 'нас', 'про', 'них', 'какая', 'много',
    'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед',
    'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда',
    'конечно', 'всю', 'между'
}

def load_stopwords(filepath):
    # Загружает стоп-слова из текстового файла (по одному слову на строку).
    # Если файл не указан или не существует, возвращает встроенный список.
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return DEFAULT_STOPWORDS

def extract_text_from_html(html_content):
    # Извлекает чистый текст из HTML-разметки.
    # Удаляет теги <script> и <style>, так как они не содержат полезного контента.
    # Возвращает строку, в которой слова разделены пробелами.
    soup = BeautifulSoup(html_content, 'lxml')
    # Удаляем скрипты и стили
    for script in soup(['script', 'style']):
        script.decompose()
    return soup.get_text(separator=' ')

def tokenize(text):
    # Разбивает текст на токены.
    # Токен — последовательность букв длиной не менее 2 символов.
    # Возвращает список слов в нижнем регистре.

    # Регулярное выражение ищет слова из букв (включая букву ё) длиной >= 2
    return re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())

def lemmatize_tokens(tokens, morph):
    # Приводит каждый токен к нормальной форме (лемме) с помощью pymorphy2.
    # Возвращает список лемм.
    lemmas = []
    for token in tokens:
        p = morph.parse(token)[0]   # берём первый (наиболее вероятный) вариант разбора
        lemmas.append(p.normal_form)
    return lemmas

def build_index(pages_dir, index_txt_path, output_json, stopwords_file=None):
    # Основная функция построения инвертированного индекса.
    # pages_dir      - папка с файлами страниц (например, "pages/")
    # index_txt_path - путь к файлу index.txt (содержит номера и URL)
    # output_json    - имя выходного JSON-файла с индексом
    # stopwords_file - опциональный файл со стоп-словами
    
    # Загружаем стоп-слова
    stopwords = load_stopwords(stopwords_file)

    # Читаем index.txt, извлекаем только номера документов (строки с ведущими нулями)
    doc_ids = set()
    with open(index_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if parts:
                doc_id = parts[0]          # строка, например "0001"
                doc_ids.add(doc_id)

    # Инициализируем лемматизатор для русского языка
    morph = pymorphy2.MorphAnalyzer()

    # Инвертированный индекс: термин -> множество doc_id (строки)
    index = defaultdict(set)

    # Обрабатываем каждый файл
    for doc_id in doc_ids:
        file_path = os.path.join(pages_dir, f"{doc_id}.txt")
        if not os.path.exists(file_path):
            print(f"Предупреждение: файл {file_path} не найден, пропускаем.")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Извлекаем текст из HTML
        text = extract_text_from_html(html)

        # Токенизация
        tokens = tokenize(text)

        # Удаление стоп-слов
        tokens = [t for t in tokens if t not in stopwords]

        # Лемматизация
        lemmas = lemmatize_tokens(tokens, morph)

        # Убираем дубликаты внутри документа
        unique_lemmas = set(lemmas)

        # Добавляем в индекс
        for lemma in unique_lemmas:
            index[lemma].add(doc_id)

    # Преобразуем множества в списки для JSON-сериализации
    serializable_index = {term: list(doc_ids) for term, doc_ids in index.items()}

    # Добавляем служебную информацию: список всех doc_id
    serializable_index['__all_docs'] = list(doc_ids)

    # Сохраняем в JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(serializable_index, f, ensure_ascii=False, indent=2)

    print(f"Индекс построен и сохранён в {output_json}")
    print(f"Всего терминов: {len(index)}")
    print(f"Всего документов: {len(doc_ids)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Построение инвертированного индекса')
    parser.add_argument('--pages_dir', required=True, help='Папка с файлами страниц (например, pages/)')
    parser.add_argument('--index_txt', required=True, help='Путь к index.txt')
    parser.add_argument('--output', default='inverted_index.json', help='Имя выходного JSON-файла')
    parser.add_argument('--stopwords', help='Файл со стоп-словами (по умолчанию встроенный список)')
    args = parser.parse_args()

    build_index(args.pages_dir, args.index_txt, args.output, args.stopwords)