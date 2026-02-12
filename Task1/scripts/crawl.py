import argparse
import asyncio
from pathlib import Path
import zipfile
import aiohttp

def load_urls(path: str) -> list[str]:
    #Читает urls.txt:
    #- 1 URL на строку
    #- пустые строки игнорируем
    #- строки, начинающиеся с #, считаем комментариями
    urls: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            urls.append(s)
    return urls

def clean_dump_dir(dump_dir: Path) -> None:
    #Опционально очищает dump/ от старых .txt, чтобы:
    #- не путаться при проверке
    #- архив точно содержал только актуальные файлы
    if not dump_dir.exists():
        return
    for p in dump_dir.glob("*.txt"):
        try:
            p.unlink()
        except OSError:
            pass

def make_zip_from_files(
    files: list[Path],
    zip_path: Path,
    folder_name_in_zip: str,
    flat: bool,
) -> None:
    #Создаёт ZIP-архив и добавляет в него только перечисленные файлы.
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    compression = zipfile.ZIP_DEFLATED

    with zipfile.ZipFile(zip_path, mode="w", compression=compression) as zf:
        for f in files:
            if flat:
                arcname = f.name
            else:
                arcname = f"{folder_name_in_zip}/{f.name}"  # относительный путь в архиве
            zf.write(f, arcname=arcname)

async def fetch_and_save(
    session: aiohttp.ClientSession,
    url: str,
    out_path: Path,
    timeout_sec: int,
) -> bool:
    #Скачивает страницу по URL и сохраняет в файл как есть (включая HTML-разметку).
    #Возвращает True, если:
    #- HTTP статус 200
    #- Content-Type похож на HTML
    #- файл успешно записан
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        async with session.get(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            # Проверяем, что это HTML (а не js/css/картинка и т.п.)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if ("text/html" not in ctype) and ("application/xhtml+xml" not in ctype):
                return False
            # Сохраняем байты “как пришло”, чтобы не ломать кодировку
            data = await resp.read()
            out_path.write_bytes(data)
            return True
    except Exception:
        return False

async def main_async(args) -> None:
    #Основной сценарий:
    #1) читаем urls.txt
    #2) скачиваем страницы
    #3) кладём их в dump/NNNN.txt
    #4) создаём index.txt: NNNN <tab> URL
    #5) делаем ZIP архив с ровно теми файлами, которые скачались
    urls = load_urls(args.urls)
    # Папка для “выкачки”
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.clean:
        clean_dump_dir(out_dir)
    headers = {
        "User-Agent": "StudentCrawler/1.0 (contact: your_email@example.com)",
        "Accept": "text/html,application/xhtml+xml",
    }

    saved = 0
    idx_lines: list[str] = []
    # Список файлов, которые реально скачались
    saved_files: list[Path] = []
    connector = aiohttp.TCPConnector(limit=args.concurrency)
    sem = asyncio.Semaphore(args.concurrency)

    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        for url in urls:
            if saved >= args.limit:
                break
            file_name = f"{saved + 1:04d}.txt"
            out_path = out_dir / file_name
            async with sem:
                ok = await fetch_and_save(session, url, out_path, args.timeout)
            # Чтобы было видно прогресс
            print(f"[{saved + 1:04d}] {'OK' if ok else 'SKIP'} {url}", flush=True)
            if ok:
                saved += 1
                idx_lines.append(f"{saved:04d}\t{url}\n")
                saved_files.append(out_path)
            await asyncio.sleep(args.delay)

    # Записываем index.txt
    Path(args.index).write_text("".join(idx_lines), encoding="utf-8")
    # Делаем архив
    if args.zip:
        zip_path = Path(args.zip_name)
        make_zip_from_files(
            files=saved_files,
            zip_path=zip_path,
            folder_name_in_zip=out_dir.name,
            flat=args.zip_flat,
        )
        print(f"Archive created: {zip_path.resolve()}", flush=True)

    if saved < args.limit:
        print(f"WARNING: удалось скачать только {saved} страниц из {args.limit}.", flush=True)

    print(f"Saved pages: {saved}", flush=True)
    print(f"Index written to: {args.index}", flush=True)
    print(f"Dump folder: {out_dir.resolve()}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    # Вход
    ap.add_argument("--urls", default="urls.txt", help="Файл со списком URL (1 URL на строку)")
    ap.add_argument("--limit", type=int, default=100, help="Сколько страниц скачать (цель)")
    # Выход
    ap.add_argument("--out", default="dump", help="Папка для сохранения HTML-страниц")
    ap.add_argument("--index", default="index.txt", help="Файл-индекс: номер файла -> URL")
    # Настройки вежливости/стабильности
    ap.add_argument("--concurrency", type=int, default=2, help="Параллельные запросы")
    ap.add_argument("--delay", type=float, default=0.5, help="Пауза между запросами (сек)")
    ap.add_argument("--timeout", type=int, default=30, help="Таймаут запроса (сек)")

    # Архивирование
    ap.add_argument("--zip", action="store_true", help="Создать zip-архив после завершения")
    ap.add_argument("--zip-name", default="dump.zip", help="Имя zip-архива (по умолчанию dump.zip)")
    ap.add_argument(
        "--zip-flat",
        action="store_true",
        help="Класть файлы в корень архива (без папки dump/ внутри)",
    )

    # Очистка старых файлов
    ap.add_argument(
        "--clean",
        action="store_true",
        help="Перед скачиванием удалить старые *.txt из dump/ (чтобы не было хвостов)",
    )

    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
