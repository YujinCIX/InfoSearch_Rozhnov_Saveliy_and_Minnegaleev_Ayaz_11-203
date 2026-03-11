import os
import math
from pathlib import Path
from collections import defaultdict, Counter

# Пути к файлам
DUMP_PATH = Path("../dump/dump")  # исходные документы
TOKENS_DIR = Path("../processed/tokens")  # файлы с токенами
LEMMAS_DIR = Path("../processed/lemmas")  # файлы с леммами

# Создаем отдельные папки для результатов
OUTPUT_DIR = Path("../tfidf_results")
TERMS_OUTPUT_DIR = OUTPUT_DIR / "terms"  # папка для терминов
LEMMAS_OUTPUT_DIR = OUTPUT_DIR / "lemmas"  # папка для лемм

# Создаем все необходимые директории
OUTPUT_DIR.mkdir(exist_ok=True)
TERMS_OUTPUT_DIR.mkdir(exist_ok=True)
LEMMAS_OUTPUT_DIR.mkdir(exist_ok=True)


def load_tokens(doc_num):
    """Загружает токены из файла (каждый токен на новой строке)"""
    token_file = TOKENS_DIR / f"{doc_num:04d}_tokens.txt"

    if not token_file.exists():
        print(f"Предупреждение: файл {token_file} не найден")
        return []

    with open(token_file, 'r', encoding='utf-8') as f:
        # Читаем все токены (каждый на новой строке)
        return [line.strip() for line in f if line.strip()]


def load_lemmas(doc_num):
    """
    Загружает леммы из файла.
    Формат файла: лемма токен1 токен2 токен3 ...
    Возвращает словарь {лемма: количество_вхождений}
    """
    lemma_file = LEMMAS_DIR / f"{doc_num:04d}_lemmas.txt"

    if not lemma_file.exists():
        print(f"Предупреждение: файл {lemma_file} не найден")
        return {}

    lemma_counts = {}
    with open(lemma_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split()
                if parts:
                    lemma = parts[0]
                    tokens = parts[1:] if len(parts) > 1 else []
                    # Сохраняем количество вхождений леммы
                    lemma_counts[lemma] = len(tokens)

    return lemma_counts


def calculate_tf_for_terms(tokens):
    """
    Считает TF для каждого термина.
    TF = частота термина / общее количество терминов
    Возвращает словарь {термин: tf}
    """
    total_terms = len(tokens)
    term_counts = Counter(tokens)

    tf = {}
    for term, count in term_counts.items():
        tf[term] = count / total_terms

    return tf, total_terms


def calculate_tf_for_lemmas(lemma_counts, total_terms):
    """
    Считает TF для каждой леммы.
    TF = количество вхождений леммы / общее количество терминов
    """
    tf = {}
    for lemma, count in lemma_counts.items():
        tf[lemma] = count / total_terms

    return tf


def calculate_idf_for_terms(all_docs_terms, total_docs):
    """
    Считает IDF для каждого термина на основе всех документов.
    IDF = log(общее количество документов / количество документов с термином)
    """
    # Считаем, в скольких документах встречается каждый термин
    term_doc_count = defaultdict(int)

    for terms_in_doc in all_docs_terms:
        # Берем уникальные термины в документе
        unique_terms = set(terms_in_doc)
        for term in unique_terms:
            term_doc_count[term] += 1

    # Считаем IDF
    idf = {}
    for term, doc_count in term_doc_count.items():
        idf[term] = math.log(total_docs / doc_count)

    return idf


def calculate_idf_for_lemmas(all_docs_lemma_counts, total_docs):
    """
    Считает IDF для каждой леммы на основе всех документов.
    """
    # Считаем, в скольких документах встречается каждая лемма
    lemma_doc_count = defaultdict(int)

    for lemma_counts in all_docs_lemma_counts:
        for lemma in lemma_counts.keys():
            lemma_doc_count[lemma] += 1

    # Считаем IDF
    idf = {}
    for lemma, doc_count in lemma_doc_count.items():
        idf[lemma] = math.log(total_docs / doc_count)

    return idf


def save_tfidf_terms(doc_num, term_tf, term_idf):
    """
    Сохраняет TF-IDF для терминов в требуемом формате:
    <термин><пробел><idf><пробел><tf-idf><\n>
    """
    output_file = TERMS_OUTPUT_DIR / f"{doc_num:04d}_terms_tfidf.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        for term, tf in term_tf.items():
            idf = term_idf.get(term, 0)
            tfidf = tf * idf
            f.write(f"{term} {idf:.6f} {tfidf:.6f}\n")

    return output_file


def save_tfidf_lemmas(doc_num, lemma_tf, lemma_idf):
    """
    Сохраняет TF-IDF для лемм в требуемом формате:
    <лемма><пробел><idf><пробел><tf-idf><\n>
    """
    output_file = LEMMAS_OUTPUT_DIR / f"{doc_num:04d}_lemmas_tfidf.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        for lemma, tf in lemma_tf.items():
            idf = lemma_idf.get(lemma, 0)
            tfidf = tf * idf
            f.write(f"{lemma} {idf:.6f} {tfidf:.6f}\n")

    return output_file


def main():
    print("=" * 70)
    print("ПОДСЧЕТ TF-IDF ДЛЯ ТЕРМИНОВ И ЛЕММ")
    print("=" * 70)

    # Получаем список всех документов по файлам в папке с токенами
    token_files = sorted(TOKENS_DIR.glob("*_tokens.txt"))
    doc_numbers = [int(f.name.replace('_tokens.txt', '')) for f in token_files]

    if not doc_numbers:
        print("Ошибка: не найдены файлы с токенами!")
        print(f"Проверьте папку: {TOKENS_DIR.absolute()}")
        return

    # Собираем данные со всех документов для расчета IDF
    all_docs_terms = []  # список списков терминов для каждого документа
    all_docs_lemma_counts = []  # список словарей {лемма: количество} для каждого документа
    all_docs_tokens_count = []  # общее количество терминов в каждом документе

    #Сбор данных

    for i, doc_num in enumerate(doc_numbers, 1):

        # Загружаем токены
        tokens = load_tokens(doc_num)
        all_docs_terms.append(tokens)
        all_docs_tokens_count.append(len(tokens))

        # Загружаем леммы
        lemma_counts = load_lemmas(doc_num)
        all_docs_lemma_counts.append(lemma_counts)

    #Расчет IDF для терминов и лемм

    # Расчет IDF для терминов
    term_idf = calculate_idf_for_terms(all_docs_terms, len(doc_numbers))

    # Расчет IDF для лемм
    lemma_idf = calculate_idf_for_lemmas(all_docs_lemma_counts, len(doc_numbers))

    #Расчет TF и сохранение TF-IDF для каждого документа

    for i, doc_num in enumerate(doc_numbers, 1):

        # Загружаем токены и леммы для этого документа
        tokens = all_docs_terms[i - 1]
        lemma_counts = all_docs_lemma_counts[i - 1]
        total_terms = all_docs_tokens_count[i - 1]

        # Расчет TF для терминов
        term_tf, _ = calculate_tf_for_terms(tokens)

        # Расчет TF для лемм
        lemma_tf = calculate_tf_for_lemmas(lemma_counts, total_terms)

        # Сохраняем результаты
        save_tfidf_terms(doc_num, term_tf, term_idf)
        save_tfidf_lemmas(doc_num, lemma_tf, lemma_idf)



if __name__ == "__main__":
    main()