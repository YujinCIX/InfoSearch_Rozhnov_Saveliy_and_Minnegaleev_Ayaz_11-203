import os
import re
from bs4 import BeautifulSoup
import pymorphy3
from nltk.corpus import stopwords
import nltk

DUMP_PATH = '../dump/dump'
TOKENS_FILE = "../tokens.txt"
LEMMAS_FILE = "../lemmas.txt"

nltk.download("stopwords")
russian_stopwords = set(stopwords.words("russian"))


morph = pymorphy3.MorphAnalyzer()


def load_texts(path):
    texts = []
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        with open(file_path, encoding="utf-8") as f:
            texts.append(f.read())
    return texts


def remove_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")


def tokenize(text):
    text = text.lower()
    tokens = re.findall(r"[а-яё]+", text)
    return tokens


def remove_stopwords(tokens):
    return [t for t in tokens if t not in russian_stopwords]


def save_tokens(tokens):
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        for token in sorted(tokens):
            f.write(token + "\n")


def lemmatize(tokens):
    lemmas = {}
    for token in tokens:
        lemma = morph.parse(token)[0].normal_form
        if lemma not in lemmas:
            lemmas[lemma] = []
        lemmas[lemma].append(token)
    return lemmas


def save_lemmas(lemmas):
    with open(LEMMAS_FILE, "w", encoding="utf-8") as f:
        for lemma in sorted(lemmas.keys()):
            line = lemma + " " + " ".join(sorted(lemmas[lemma]))
            f.write(line + "\n")


def main():
    texts = load_texts(DUMP_PATH)

    all_tokens = []

    for text in texts:
        text = remove_html(text)
        tokens = tokenize(text)
        tokens = remove_stopwords(tokens)
        all_tokens.extend(tokens)

    unique_tokens = list(set(all_tokens))

    save_tokens(unique_tokens)

    lemmas = lemmatize(unique_tokens)
    save_lemmas(lemmas)

    print("Созданы tokens.txt и lemmas.txt")


if __name__ == "__main__":
    main()
