from flask import Flask, render_template, request
from vector_search import load_tfidf, build_vocab, build_doc_vectors, search
import urllib.parse

TFIDF_FOLDER = "tfidf_results"
LINKS_FILE = "index.txt"

app = Flask(__name__)

# ======= ЗАГРУЗКА =======
docs, idf = load_tfidf(TFIDF_FOLDER)
vocab, term_index = build_vocab(docs)
doc_vectors = build_doc_vectors(docs, term_index)

# ======= ЗАГРУЗКА ССЫЛОК =======
def load_links(file_path):
    links = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 2:
                continue

            doc_id, url = parts
            links[doc_id] = url

    print(f"🔗 Загружено ссылок: {len(links)}")
    return links

links = load_links(LINKS_FILE)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        print("\n======================")
        print("💬 QUERY:", query)

        if query:
            raw_results = search(query, doc_vectors, idf, term_index)

            for doc, score in raw_results:
                if score <= 0:
                    continue

                doc_id = doc.split("_")[0]
                url = links.get(doc_id, "#")

                title = urllib.parse.unquote(url.split("/")[-1])

                results.append({
                    "title": title,
                    "score": round(score, 4),
                    "url": url
                })

            if not results:
                print("⚠️ Все результаты = 0")

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)