import re
from pathlib import Path
from typing import Set, Dict, List, Union

# Попытка импорта лемматизатора 
try:
    from pymorphy2 import MorphAnalyzer
    MORPH_AVAILABLE = True
except ImportError:
    MORPH_AVAILABLE = False
    print("Предупреждение: pymorphy2 не установлен. Лемматизация отключена.")

# Пути к файлам
INDEX_FILE = Path("inverted_index.txt")   # инвертированный индекс
LINKS_FILE = Path("index.txt")            # соответствие номеров и ссылок


class BooleanSearch:
    """
    Класс для булева поиска по инвертированному индексу.
    """

    def __init__(self, index_file: Path, links_file: Path):
        """
        Инициализация: загрузка индекса, ссылок и подготовка лемматизатора.
        """
        self.index: Dict[str, Set[int]] = {}   # лемма -> множество номеров документов
        self.all_docs: Set[int] = set()        # множество всех документов (для NOT)
        self.links: Dict[int, str] = {}        # номер документа -> URL

        # Инициализация лемматизатора (если доступен)
        self.morph = MorphAnalyzer() if MORPH_AVAILABLE else None

        self.load_index(index_file)
        self.load_links(links_file)

    def load_index(self, index_file: Path) -> None:
        """
        Загружает инвертированный индекс из файла.
        Формат каждой строки: <лемма> <номер1> <номер2> ...
        """
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        print(f"Предупреждение: строка {line_num} в {index_file} пропущена (мало частей)")
                        continue
                    lemma = parts[0]
                    # Преобразуем остальные части в целые числа (номера документов)
                    docs = set()
                    for doc_str in parts[1:]:
                        try:
                            docs.add(int(doc_str))
                        except ValueError:
                            print(f"Предупреждение: неверный номер документа '{doc_str}' в строке {line_num}")
                    self.index[lemma] = docs
                    self.all_docs.update(docs)
            print(f"Загружен индекс: {len(self.index)} лемм, {len(self.all_docs)} документов.")
        except FileNotFoundError:
            print(f"Ошибка: файл индекса {index_file} не найден.")
            raise

    def load_links(self, links_file: Path) -> None:
        """
        Загружает соответствие номеров документов и URL из index.txt.
        Формат строки: <номер_документа>\t<URL>
        """
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    if '\t' not in line:
                        print(f"Предупреждение: строка {line_num} в {links_file} не содержит табуляции, пропущена.")
                        continue
                    doc_str, url = line.split('\t', 1)
                    try:
                        doc_num = int(doc_str)
                        self.links[doc_num] = url
                    except ValueError:
                        print(f"Предупреждение: неверный номер документа '{doc_str}' в строке {line_num}")

            # Проверим, есть ли ссылки для всех документов из индекса
            missing = self.all_docs - set(self.links.keys())
            if missing:
                print(f"Внимание: для документов {sorted(missing)} отсутствуют ссылки.")
            print(f"Загружено ссылок: {len(self.links)}")
        except FileNotFoundError:
            print(f"Ошибка: файл ссылок {links_file} не найден. Ссылки будут недоступны.")
            self.links = {}

    def lemmatize(self, word: str) -> str:
        """
        Приводит слово к нормальной форме (лемме).
        Если лемматизатор недоступен, возвращает слово в нижнем регистре.
        """
        if self.morph is not None:
            # pymorphy2 возвращает список разборов; берём нормальную форму первого
            return self.morph.parse(word)[0].normal_form
        return word.lower()

    def tokenize_query(self, query: str) -> List[str]:
        """
        Разбивает запрос на токены: операторы, скобки, ключевые слова.
        Расставляет пробелы вокруг скобок для удобства.
        """
        # Добавляем пробелы вокруг скобок
        query = query.replace('(', ' ( ').replace(')', ' ) ')
        # Разделяем по пробелам и удаляем пустые токены
        tokens = [t for t in query.split() if t]
        return tokens

    def infix_to_postfix(self, tokens: List[str]) -> List[str]:
        """
        Преобразует инфиксную запись в постфиксную (обратную польскую нотацию)
        с использованием алгоритма сортировочной станции.
        Поддерживаются операторы: NOT (унарный), AND, OR.
        """
        precedence = {
            'not': 3,   # наивысший приоритет (унарный)
            'and': 2,
            'or': 1,
            '(': 0,
            ')': 0
        }
        output = []
        stack = []

        for token in tokens:
            if token == '(':
                stack.append(token)
            elif token == ')':
                # Выталкиваем все операторы до открывающей скобки
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()  # удаляем '('
                else:
                    raise ValueError("Несбалансированные скобки")
            elif token in precedence:  # оператор
                # Пока в стеке есть оператор с большим или равным приоритетом, выталкиваем его
                while (stack and stack[-1] != '(' and
                       precedence.get(stack[-1], 0) >= precedence[token]):
                    output.append(stack.pop())
                stack.append(token)
            else:  # термин (слово)
                output.append(token)

        # Выталкиваем оставшиеся операторы
        while stack:
            op = stack.pop()
            if op == '(' or op == ')':
                raise ValueError("Несбалансированные скобки")
            output.append(op)

        return output

    def evaluate_postfix(self, postfix: List[str]) -> Set[int]:
        """
        Вычисляет значение выражения в постфиксной записи.
        Для каждого терма применяет лемматизацию и получает множество документов из индекса.
        """
        stack = []

        for token in postfix:
            if token == 'and':
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для AND")
                right = stack.pop()
                left = stack.pop()
                stack.append(left & right)
            elif token == 'or':
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для OR")
                right = stack.pop()
                left = stack.pop()
                stack.append(left | right)
            elif token == 'not':
                if len(stack) < 1:
                    raise ValueError("Недостаточно операндов для NOT")
                operand = stack.pop()
                stack.append(self.all_docs - operand)
            else:  # термин – применяем лемматизацию
                # Очищаем от пунктуации (на случай, если слово пришло с запятой и т.п.)
                clean_token = re.sub(r'[^\w\s]', '', token)
                if not clean_token:
                    clean_token = token  # если осталась пустота, оставляем как есть
                lemma = self.lemmatize(clean_token)
                docs = self.index.get(lemma, set())
                stack.append(docs)

        if len(stack) != 1:
            raise ValueError("Некорректное выражение: осталось несколько значений в стеке")

        return stack[0]

    def parse_query(self, query: str) -> Union[Set[int], str]:
        """
        Основной метод: принимает строку запроса, возвращает множество номеров документов
        или сообщение об ошибке.
        """
        query = query.strip()
        if not query:
            return "Пустой запрос"

        try:
            tokens = self.tokenize_query(query)
            postfix = self.infix_to_postfix(tokens)
            result = self.evaluate_postfix(postfix)
            return result
        except Exception as e:
            return f"Ошибка при обработке запроса: {e}"

    def format_results(self, result: Union[Set[int], str]) -> str:
        """
        Форматирует результат для вывода пользователю: количество, список с номерами и ссылками.
        """
        if isinstance(result, str):
            return result  # сообщение об ошибке
        if not result:
            return "Документы не найдены."

        sorted_docs = sorted(result)
        lines = [f"Найдено документов: {len(sorted_docs)}", "-" * 60]

        for i, doc_num in enumerate(sorted_docs, 1):
            link = self.links.get(doc_num, "ссылка не найдена")
            lines.append(f"{i:3}. Документ {doc_num:04d}: {link}")
            # Ограничим вывод, если документов очень много
            if i >= 50 and len(sorted_docs) > 50:
                lines.append(f"\n... и ещё {len(sorted_docs) - 50} документов")
                break

        return "\n".join(lines)

    def interactive_search(self):
        """
        Запускает интерактивный режим поиска.
        """
        print("\n" + "=" * 70)
        print("БУЛЕВ ПОИСК ПО ИНВЕРТИРОВАННОМУ ИНДЕКСУ (с лемматизацией)")
        print("=" * 70)
        print("\nПоддерживаемые операторы: AND, OR, NOT (регистр не важен).")
        print("Можно использовать круглые скобки для группировки.")
        print("\nПримеры запросов:")
        print("  кот AND собака")
        print("  (клеопатра AND цезарь) OR (антоний AND цицерон)")
        print("  компьютер NOT (игра OR развлечение)")
        print("\nДля выхода введите 'exit' или 'quit'.")
        print("-" * 70)

        while True:
            try:
                query = input("Запрос > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nДо свидания!")
                break

            if query.lower() in ('exit', 'quit', 'выход'):
                print("До свидания!")
                break
            if not query:
                continue

            print("\nРезультат:")
            result = self.parse_query(query)
            print(self.format_results(result))
            print("-" * 70)


def main():
    """
    Точка входа: проверяет наличие файлов и запускает поиск.
    """
    if not INDEX_FILE.exists():
        print(f"Ошибка: файл индекса {INDEX_FILE} не найден.")
        print("Сначала запустите build_index.py для построения индекса.")
        return

    if not LINKS_FILE.exists():
        print(f"Ошибка: файл ссылок {LINKS_FILE} не найден.")
        print("Убедитесь, что index.txt (из задания 1) присутствует.")
        return

    try:
        searcher = BooleanSearch(INDEX_FILE, LINKS_FILE)
        searcher.interactive_search()
    except Exception as e:
        print(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
