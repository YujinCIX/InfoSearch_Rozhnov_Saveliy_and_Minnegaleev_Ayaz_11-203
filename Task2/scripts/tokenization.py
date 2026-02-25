import os
import re
from bs4 import BeautifulSoup
import pymorphy3
from nltk.corpus import stopwords
import nltk
from pathlib import Path

DUMP_PATH = '../dump/dump'
# Создаем директории для выходных файлов
OUTPUT_DIR = Path("../processed")
TOKENS_DIR = OUTPUT_DIR / "tokens"
LEMMAS_DIR = OUTPUT_DIR / "lemmas"

nltk.download("stopwords")
russian_stopwords = set(stopwords.words("russian"))

morph = pymorphy3.MorphAnalyzer()


def load_texts(path):
    texts = []
    filenames = []
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        with open(file_path, encoding="utf-8") as f:
            texts.append(f.read())
            filenames.append(filename)
    return texts, filenames


def remove_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")


def tokenize(text):
    text = text.lower()
    tokens = re.findall(r"[а-яё]+", text)
    return tokens


def remove_stopwords(tokens):
    return [t for t in tokens if t not in russian_stopwords]


def save_tokens(tokens, filename):
    # Изменяем расширение файла на .txt
    output_file = TOKENS_DIR / f"{Path(filename).stem}_tokens.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for token in sorted(tokens):
            f.write(token + "\n")
    return output_file


def lemmatize(tokens):
    lemmas = {}
    for token in tokens:
        lemma = morph.parse(token)[0].normal_form
        if lemma not in lemmas:
            lemmas[lemma] = []
        lemmas[lemma].append(token)
    return lemmas


def save_lemmas(lemmas, filename):
    # Изменяем расширение файла на .txt
    output_file = LEMMAS_DIR / f"{Path(filename).stem}_lemmas.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for lemma in sorted(lemmas.keys()):
            # Получаем уникальные токены для каждой леммы
            unique_tokens = sorted(set(lemmas[lemma]))
            line = lemma + " " + " ".join(unique_tokens)
            f.write(line + "\n")
    return output_file


def main():
    texts, filenames = load_texts(DUMP_PATH)

    print(f"Найдено файлов: {len(texts)}")

    for i, (text, filename) in enumerate(zip(texts, filenames), 1):
        print(f"Обработка файла {i}/{len(texts)}: {filename}")

        # Обработка текста
        text = remove_html(text)
        tokens = tokenize(text)
        tokens = remove_stopwords(tokens)

        # Сохраняем токены для текущего файла
        unique_tokens = list(set(tokens))
        token_file = save_tokens(unique_tokens, filename)
        print(f"  Токены сохранены в: {token_file}")

        # Лемматизируем и сохраняем леммы для текущего файла
        lemmas = lemmatize(unique_tokens)
        lemma_file = save_lemmas(lemmas, filename)
        print(f"  Леммы сохранены в: {lemma_file}")

    print(f"\nОбработка завершена!")
    print(f"Файлы с токенами сохранены в: {TOKENS_DIR}")
    print(f"Файлы с леммами сохранены в: {LEMMAS_DIR}")


if __name__ == "__main__":
    main()