import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Union, Tuple

# Пути
INDEX_FILE = Path("inverted_index.txt")
LINKS_FILE = Path("index.txt")  # файл с соответствием номеров и ссылок


class BooleanSearch:
    def __init__(self, index_file: Path, links_file: Path):
        """Инициализация поиска: загрузка индекса и ссылок"""
        self.index: Dict[str, Set[int]] = {}
        self.all_docs: Set[int] = set()
        self.links: Dict[int, str] = {}  # словарь {номер_документа: ссылка}

        self.load_index(index_file)
        self.load_links(links_file)

    def load_index(self, index_file: Path):
        """Загрузка инвертированного индекса из файла"""


        with open(index_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        term = parts[0]
                        # Преобразуем строки с номерами документов в множество int
                        docs = set(int(doc) for doc in parts[1:])
                        self.index[term] = docs
                        self.all_docs.update(docs)


    def load_links(self, links_file: Path):
        """Загрузка соответствия номеров документов и ссылок"""

        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '\t' in line:
                        # Формат: номер_документа<TAB>ссылка
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            doc_num = int(parts[0])
                            link = parts[1]
                            self.links[doc_num] = link



            # Проверяем, есть ли ссылки для всех документов
            missing_links = self.all_docs - set(self.links.keys())
            if missing_links:
                print(f"Внимание: нет ссылок для документов: {sorted(missing_links)}")

        except FileNotFoundError:
            print(f"Ошибка: файл {links_file} не найден!")
            self.links = {}

    def parse_query(self, query: str) -> Union[Set[int], str]:
        """
        Парсит и выполняет булев запрос.
        Поддерживает операторы AND, OR, NOT и скобки.
        """
        # Удаляем лишние пробелы и приводим к нижнему регистру
        query = query.strip().lower()

        if not query:
            return "Пустой запрос"

        try:
            # Токенизируем запрос
            tokens = self.tokenize_query(query)

            # Преобразуем инфиксную запись в постфиксную (обратная польская нотация)
            postfix = self.infix_to_postfix(tokens)

            # Вычисляем результат
            result = self.evaluate_postfix(postfix)

            return result

        except Exception as e:
            return f"Ошибка в запросе: {e}"

    def tokenize_query(self, query: str) -> List[str]:
        """
        Разбивает запрос на токены (термины, операторы, скобки)
        """
        # Добавляем пробелы вокруг скобок для удобства токенизации
        query = query.replace('(', ' ( ').replace(')', ' ) ')

        # Разбиваем на токены
        tokens = []
        for token in query.split():
            if token:  # пропускаем пустые
                tokens.append(token)

        return tokens

    def infix_to_postfix(self, tokens: List[str]) -> List[str]:
        """
        Преобразует инфиксную запись в постфиксную (алгоритм сортировочной станции)
        """
        # Приоритет операторов
        precedence = {
            'not': 3,
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

            elif token in precedence:  # это оператор
                while (stack and stack[-1] != '(' and
                       precedence.get(stack[-1], 0) >= precedence.get(token, 0)):
                    output.append(stack.pop())
                stack.append(token)

            else:  # это термин
                output.append(token)

        # Выталкиваем оставшиеся операторы
        while stack:
            output.append(stack.pop())

        return output

    def evaluate_postfix(self, postfix: List[str]) -> Set[int]:
        """
        Вычисляет значение выражения в постфиксной записи
        """
        stack = []

        for token in postfix:
            if token == 'and':
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для AND")
                right = stack.pop()
                left = stack.pop()
                result = self.and_operation(left, right)
                stack.append(result)

            elif token == 'or':
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для OR")
                right = stack.pop()
                left = stack.pop()
                result = self.or_operation(left, right)
                stack.append(result)

            elif token == 'not':
                if len(stack) < 1:
                    raise ValueError("Недостаточно операндов для NOT")
                operand = stack.pop()
                result = self.not_operation(operand)
                stack.append(result)

            else:  # это термин
                # Получаем множество документов для термина
                docs = self.index.get(token, set())
                stack.append(docs)

        if len(stack) != 1:
            raise ValueError("Некорректное выражение")

        return stack[0]

    def and_operation(self, set1: Set[int], set2: Set[int]) -> Set[int]:
        """Операция AND: пересечение множеств"""
        return set1 & set2

    def or_operation(self, set1: Set[int], set2: Set[int]) -> Set[int]:
        """Операция OR: объединение множеств"""
        return set1 | set2

    def not_operation(self, docs: Set[int]) -> Set[int]:
        """Операция NOT: дополнение множества"""
        return self.all_docs - docs

    def format_results(self, result: Union[Set[int], str]) -> str:
        """Форматирует результаты для вывода с ссылками"""
        if isinstance(result, str):  # сообщение об ошибке
            return result

        if not result:
            return "Документы не найдены"

        # Сортируем результаты
        sorted_results = sorted(result)

        # Форматируем вывод
        output = [f"Найдено документов: {len(sorted_results)}"]
        output.append("-" * 60)

        for i, doc_num in enumerate(sorted_results, 1):
            # Получаем ссылку для документа
            link = self.links.get(doc_num, "Ссылка не найдена")


            output.append(f"{i:3}. Документ {doc_num:04d}: {link}")

            # Ограничиваем вывод для очень больших результатов
            if i >= 50 and len(sorted_results) > 50:
                output.append(f"\n... и еще {len(sorted_results) - 50} документов")
                break

        return "\n".join(output)

    def search_interactive(self):
        """Интерактивный режим поиска"""
        print("\n" + "=" * 70)
        print("БУЛЕВ ПОИСК С ССЫЛКАМИ НА ДОКУМЕНТЫ")
        print("=" * 70)
        print("\nПоддерживаемые операторы:")
        print("  AND - логическое И")
        print("  OR  - логическое ИЛИ")
        print("  NOT - логическое НЕ")
        print("\nМожно использовать скобки для группировки")
        print("\nПримеры запросов:")
        print('  кот AND собака')
        print('  (клеопатра AND цезарь) OR (антоний AND цицерон)')
        print('  компьютер NOT (игра OR развлечение)')
        print("\nДля выхода введите 'exit' или 'quit'")

        while True:
            print("\n" + "-" * 70)
            query = input("Введите запрос: ").strip()

            if query.lower() in ['exit', 'quit', 'выход']:
                print("До свидания!")
                break

            if not query:
                continue

            print("\nРезультат поиска:")
            result = self.parse_query(query)
            print(self.format_results(result))


def main():
    # Проверяем существование файлов
    if not INDEX_FILE.exists():
        print(f"Ошибка: файл индекса {INDEX_FILE} не найден!")
        return

    if not LINKS_FILE.exists():
        print(f"Ошибка: файл со ссылками {LINKS_FILE} не найден!")
        return

    # Создаем поисковую систему
    search = BooleanSearch(INDEX_FILE, LINKS_FILE)

    # Запускаем интерактивный режим
    search.search_interactive()


if __name__ == "__main__":
    main()