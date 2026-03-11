import os
from pathlib import Path
from collections import defaultdict

# Пути
LEMMAS_DIR = Path("lemmas")  # папка с файлами лемм
OUTPUT_FILE = Path("inverted_index.txt")  # выходной файл


def create_inverted_index():
    """Создает инвертированный индекс на основе файлов с леммами"""

    index = defaultdict(list)

    # Проверяем, существует ли папка с леммами
    if not LEMMAS_DIR.exists():
        print(f"Ошибка: папка {LEMMAS_DIR} не найдена!")
        return None

    # Получаем все файлы с леммами (*_lemmas.txt)
    lemma_files = list(LEMMAS_DIR.glob("*_lemmas.txt"))

    print(f"Найдено файлов с леммами: {len(lemma_files)}")

    if not lemma_files:
        print("Нет файлов для обработки!")
        return None

    # Сортируем файлы по имени (0001, 0002, 0003...)
    lemma_files.sort()

    for lemma_file in lemma_files:
        # Получаем номер документа из имени файла и преобразуем в int
        # "0001_lemmas.txt" -> "0001" -> 1
        doc_num = int(lemma_file.name.replace('_lemmas.txt', ''))

        print(f"Обработка документа {doc_num:04d}")  # выводим с ведущими нулями

        # Читаем леммы из файла
        with open(lemma_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Формат файла: "лемма токен1 токен2 токен3 ..."
                    parts = line.split()
                    if parts:
                        lemma = parts[0]  # первое слово - это лемма
                        # Добавляем номер документа в индекс для этой леммы
                        if doc_num not in index[lemma]:
                            index[lemma].append(doc_num)

    return index


def save_index_simple(index):
    """Сохраняет индекс в самом простом формате"""

    if index is None:
        print("Нет данных для сохранения!")
        return

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Сортируем леммы по алфавиту
        for lemma in sorted(index.keys()):
            # Сортируем номера документов (теперь они int)
            docs = ' '.join(str(d) for d in sorted(index[lemma]))
            f.write(f"{lemma} {docs}\n")

    print(f"\nИндекс сохранен в: {OUTPUT_FILE}")
    print(f"Всего уникальных лемм: {len(index)}")


def main():
    print("Создание инвертированного индекса лемм...")
    print(f"Поиск файлов в: {LEMMAS_DIR.absolute()}")

    index = create_inverted_index()

    if index:
        save_index_simple(index)

        # Показываем небольшой пример
        print("\nПример первых 10 лемм в индексе:")
        for i, lemma in enumerate(sorted(index.keys())[:10]):
            docs = ' '.join(str(d) for d in sorted(index[lemma])[:5])
            print(f"  {lemma}: {docs}...")

        # Показываем статистику
        all_docs = set()
        for docs in index.values():
            all_docs.update(docs)
        print(f"\nСтатистика:")
        print(f"  Всего документов: {len(all_docs)}")
        print(f"  Всего лемм: {len(index)}")


if __name__ == "__main__":
    main()