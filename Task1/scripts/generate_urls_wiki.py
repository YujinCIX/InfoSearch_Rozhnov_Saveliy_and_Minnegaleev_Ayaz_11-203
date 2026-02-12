import argparse
import time
from urllib.parse import quote

import requests


def title_to_url(lang: str, title: str) -> str:
    #Преобразует заголовок MediaWiki (title) в обычный URL статьи вида:
    #https://ru.wikipedia.org/wiki/Название_статьи
    #- в URL у Википедии пробелы обычно заменяются на подчёркивания.
    #- Дополнительно делаем percent-encoding (quote), чтобы корректно обработать спецсимволы.
    t = title.replace(" ", "_")
    return f"https://{lang}.wikipedia.org/wiki/{quote(t)}"

def main() -> None:
    #Скрипт получает список случайных статей из MediaWiki API и сохраняет их в urls.txt.
    #- По заданию нужен заранее подготовленный список страниц (100+).
    #- Этот генератор помогает быстро получить много URL в одном языке (например, ru).
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ru", help="Код языка Википедии: ru, en, de ...")
    ap.add_argument("--count", type=int, default=150, help="Сколько URL собрать (лучше с запасом > 100)")
    ap.add_argument("--out", default="urls.txt", help="Куда сохранить список URL")
    ap.add_argument("--sleep", type=float, default=0.5, help="Пауза между запросами к API (сек)")
    args = ap.parse_args()
    # API endpoint конкретной языковой Википедии
    api = f"https://{args.lang}.wikipedia.org/w/api.php"
    # Session выгоднее, чем requests.get каждый раз: переиспользуются соединения
    s = requests.Session()
    # Вежливый User-Agent (желательно указать проект и контакт)
    s.headers["User-Agent"] = "StudentCrawler/1.0 (contact: your_email@example.com)"
    urls: list[str] = []
    seen: set[str] = set()
    # MediaWiki API может возвращать продолжение (continue) — будем учитывать
    cont = None
    while len(urls) < args.count:
        params = {
            "action": "query",
            "format": "json",
            "list": "random",
            # rnnamespace=0 — основное пространство статей (без служебных страниц)
            "rnnamespace": 0,
            # Попросим пачку случайных страниц, чтобы меньше ходить в API
            "rnlimit": 50,
        }
        if cont:
            params.update(cont)

        r = s.get(api, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Из ответа забираем массив случайных страниц
        for item in data.get("query", {}).get("random", []):
            url = title_to_url(args.lang, item["title"])
            if url not in seen:
                seen.add(url)
                urls.append(url)
                if len(urls) >= args.count:
                    break
        # Если API говорит, что есть продолжение — продолжаем
        cont_data = data.get("continue")
        if not cont_data:
            break
        cont = cont_data
        # Пауза, чтобы не спамить API
        time.sleep(args.sleep)
    # Сохраняем: 1 URL на строку
    with open(args.out, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")
    print(f"Saved {len(urls)} urls to {args.out}")


if __name__ == "__main__":
    main()
