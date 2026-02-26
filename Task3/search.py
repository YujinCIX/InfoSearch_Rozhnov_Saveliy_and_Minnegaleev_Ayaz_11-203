#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import os

# Приоритеты операторов (чем больше число, тем выше приоритет)
PRECEDENCE = {
    'NOT': 3,
    'AND': 2,
    'OR': 1,
}
LEFT_ASSOC = True  # все бинарные операторы левоассоциативны (AND и OR)

def load_index(json_path):
    # Загружает индекс из JSON-файла.
    #Возвращает кортеж (index, all_docs), где:
    #    index     - словарь {термин: множество doc_id}
    #    all_docs  - множество всех номеров документов
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Извлекаем служебный список всех документов
    all_docs = set(data.pop('__all_docs', []))
    # Преобразуем списки doc_id обратно в множества для быстрых операций
    index = {term: set(doc_ids) for term, doc_ids in data.items()}
    return index, all_docs

def load_urls(index_txt_path):
    # Загружает соответствие doc_id -> url из index.txt.
    # doc_id хранятся как строки (с ведущими нулями).
    urls = {}
    with open(index_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                doc_id, url = parts
                urls[doc_id] = url
    return urls

def tokenize_query(query):
    # Разбивает строку запроса на токены.
    # Скобки выделяются в отдельные токены, операторы приводятся к верхнему регистру,
    # остальные слова — к нижнему (так как в индексе термины хранятся в нижнем регистре).
    
    # Добавляем пробелы вокруг скобок, чтобы они стали отдельными токенами
    query = query.replace('(', ' ( ').replace(')', ' ) ')
    tokens = query.split()
    result = []
    for tok in tokens:
        if tok.upper() in {'AND', 'OR', 'NOT'}:
            result.append(tok.upper())
        elif tok in {'(', ')'}:
            result.append(tok)
        else:
            result.append(tok.lower())  # термин в нижнем регистре
    return result

def infix_to_rpn(tokens):
    # Преобразует инфиксную запись (со скобками и операторами) в обратную польскую нотацию (ОПН).
    # Используется алгоритм сортировочной станции Эдсгера Дейкстры.
    output = []  # выходная очередь (ОПН)
    stack = []   # стек операторов и скобок

    for token in tokens:
        if token == '(':
            stack.append(token)
        elif token == ')':
            # Выталкиваем всё до открывающей скобки
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Несбалансированные скобки")
            stack.pop()  # удаляем '('
        elif token in PRECEDENCE:  # оператор
            # Пока на вершине стека оператор с большим или равным приоритетом (и левая ассоциативность)
            while (stack and stack[-1] != '(' and
                   (PRECEDENCE[stack[-1]] > PRECEDENCE[token] or
                    (PRECEDENCE[stack[-1]] == PRECEDENCE[token] and LEFT_ASSOC))):
                output.append(stack.pop())
            stack.append(token)
        else:  # термин (слово)
            output.append(token)

    # Выталкиваем оставшиеся операторы
    while stack:
        if stack[-1] == '(':
            raise ValueError("Несбалансированные скобки")
        output.append(stack.pop())

    return output

def evaluate_rpn(rpn, index, all_docs):
    # Вычисляет значение выражения, заданного в ОПН.
    # Операнды — множества номеров документов (строки).
    stack = []
    for token in rpn:
        if token == 'NOT':
            if not stack:
                raise ValueError("NOT требует операнда")
            operand = stack.pop()
            result = all_docs - operand   # дополнение до всех документов
            stack.append(result)
        elif token == 'AND':
            if len(stack) < 2:
                raise ValueError("AND требует двух операндов")
            right = stack.pop()
            left = stack.pop()
            stack.append(left & right)    # пересечение множеств
        elif token == 'OR':
            if len(stack) < 2:
                raise ValueError("OR требует двух операндов")
            right = stack.pop()
            left = stack.pop()
            stack.append(left | right)    # объединение множеств
        else:  # термин
            # Если термин отсутствует в индексе, возвращаем пустое множество
            stack.append(index.get(token, set()))

    if len(stack) != 1:
        raise ValueError("Ошибка вычисления выражения: в стеке осталось несколько элементов")
    return stack[0]

def boolean_search(query, index, all_docs):
    # Основная функция поиска: принимает строку запроса, возвращает множество doc_id или None с ошибкой.
    tokens = tokenize_query(query)
    try:
        rpn = infix_to_rpn(tokens)
    except ValueError as e:
        return None, str(e)
    try:
        result_docs = evaluate_rpn(rpn, index, all_docs)
    except ValueError as e:
        return None, str(e)
    return result_docs, None

def main():
    parser = argparse.ArgumentParser(description='Булев поиск по индексу')
    parser.add_argument('--index', default='inverted_index.json', help='JSON-файл индекса')
    parser.add_argument('--index_txt', required=True, help='Файл index.txt для отображения ссылок')
    args = parser.parse_args()

    # Загружаем индекс
    if not os.path.exists(args.index):
        print(f"Файл индекса {args.index} не найден. Сначала запустите build_index.py")
        return
    index, all_docs = load_index(args.index)
    urls = load_urls(args.index_txt)

    print("Булев поиск (поддерживаются AND, OR, NOT, скобки).")
    print("Пример: (Клеопатра AND Цезарь) OR (Антоний AND NOT Цицерон) OR Помпей")
    print("Для выхода введите 'exit'")

    while True:
        try:
            query = input("\nЗапрос > ").strip()
            if query.lower() == 'exit':
                break
            if not query:
                continue

            result_docs, error = boolean_search(query, index, all_docs)
            if error:
                print(f"Ошибка: {error}")
                continue

            if not result_docs:
                print("Ничего не найдено.")
            else:
                print(f"Найдено документов: {len(result_docs)}")
                # Сортируем номера для удобства (лексикографически, т.к. это строки "0001")
                for doc_id in sorted(result_docs):
                    url = urls.get(doc_id, 'URL не найден')
                    print(f"{doc_id}\t{url}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")

if __name__ == '__main__':
    main()