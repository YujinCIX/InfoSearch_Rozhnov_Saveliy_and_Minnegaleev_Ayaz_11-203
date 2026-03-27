import os
import math
import re
from collections import Counter

# ======= ЛЕММАТИЗАЦИЯ =======
try:
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
    USE_LEMMA = True
except:
    morph = None
    USE_LEMMA = False

def tokenize(text):
    return re.findall(r"[а-яa-z0-9]+", text.lower())

def lemmatize(tokens):
    if not USE_LEMMA:
        return tokens
    return [morph.parse(token)[0].normal_form for token in tokens]

# ======= ЗАГРУЗКА TF-IDF (С УЧЁТОМ ПОДПАПОК) =======
def load_tfidf(folder):
    docs = {}
    idf = {}

    print(f"📂 Загружаем TF-IDF из: {folder}")

    for root, _, files in os.walk(folder):
        for filename in files:
            path = os.path.join(root, filename)

            if not os.path.isfile(path):
                continue

            doc_vector = {}

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split()

                    if len(parts) == 3:
                        term, idf_val, tfidf_val = parts
                    elif len(parts) == 2:
                        term, tfidf_val = parts
                        idf_val = 1.0
                    else:
                        continue

                    try:
                        doc_vector[term] = float(tfidf_val)
                        idf[term] = float(idf_val)
                    except:
                        continue

            if doc_vector:
                docs[filename] = doc_vector

    print(f"✅ Загружено документов: {len(docs)}")
    print(f"📊 Уникальных терминов: {len(idf)}")

    return docs, idf

# ======= СЛОВАРЬ =======
def build_vocab(docs):
    vocab = set()
    for doc in docs.values():
        vocab.update(doc.keys())

    vocab = list(vocab)
    term_index = {term: i for i, term in enumerate(vocab)}

    print(f"📚 Размер словаря: {len(vocab)}")

    return vocab, term_index

# ======= ВЕКТОРЫ ДОКУМЕНТОВ =======
def build_doc_vectors(docs, term_index):
    vectors = {}

    for doc_id, terms in docs.items():
        vec = [0.0] * len(term_index)

        for term, tfidf in terms.items():
            if term in term_index:
                vec[term_index[term]] = tfidf

        vectors[doc_id] = vec

    print("📦 Векторы документов построены")

    return vectors

# ======= ВЕКТОР ЗАПРОСА =======
def build_query_vector(query, idf, term_index):
    tokens = tokenize(query)
    lemmas = lemmatize(tokens)

    print("🔍 TOKENS:", tokens)
    print("🔍 LEMMAS:", lemmas)

    counter = Counter(lemmas)
    total = sum(counter.values())

    vec = [0.0] * len(term_index)

    found_terms = []

    for term, count in counter.items():
        if term in term_index:
            tf = count / total
            idf_val = idf.get(term, 1.0)
            vec[term_index[term]] = tf * idf_val
            found_terms.append(term)

    if not found_terms:
        print("⚠️ НЕТ СОВПАДЕНИЙ С СЛОВАРЁМ")
    else:
        print("✅ Найдены термины:", found_terms)

    return vec

# ======= КОСИНУСНОЕ СХОДСТВО =======
def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot / (norm1 * norm2)

# ======= ПОИСК =======
def search(query, doc_vectors, idf, term_index, top_k=10):
    query_vec = build_query_vector(query, idf, term_index)

    print("📐 Сумма вектора запроса:", sum(query_vec))

    scores = []

    for doc_id, doc_vec in doc_vectors.items():
        sim = cosine_similarity(query_vec, doc_vec)
        scores.append((doc_id, sim))

    scores.sort(key=lambda x: x[1], reverse=True)

    print("🏆 ТОП результатов:", scores[:3])

    return scores[:top_k]