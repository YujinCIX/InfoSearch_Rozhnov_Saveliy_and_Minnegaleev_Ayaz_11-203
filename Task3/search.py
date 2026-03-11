import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Union

# Пути
INDEX_FILE = Path("../inverted_index.txt")


class BooleanSearch:
    def __init__(self, index_file: Path):
        """Инициализация поиска: загрузка индекса"""
        self.index: Dict[str, Set[int]] = {}
        self.all_docs: Set[int] = set()
        self.load_index(index_file)

    def load_index(self, index_file: Path):
        """Загрузка инвертированного индекса из файла"""
        print("Загрузка индекса...")

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
        """Форматирует результаты для вывода"""
        if isinstance(result, str):  # сообщение об ошибке
            return result

        if not result:
            return "Документы не найдены"

        # Сортируем результаты
        sorted_results = sorted(result)

        # Форматируем вывод
        output = [f"Найдено документов: {len(sorted_results)}"]
        output.append("Номера документов: " + ", ".join(str(d) for d in sorted_results[:20]))

        if len(sorted_results) > 20:
            output.append(f"... и еще {len(sorted_results) - 20}")

        return "\n".join(output)

    def search_interactive(self):
        print("\n" + "=" * 60)
        print("БУЛЕВ ПОИСК")
        print("=" * 60)
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
            print("\n" + "-" * 60)
            query = input("Введите запрос: ").strip()

            if query.lower() in ['exit', 'quit', 'выход']:
                print("До свидания!")
                break

            if not query:
                continue

            print("\nРезультат:")
            result = self.parse_query(query)
            print(self.format_results(result))


def main():
    # Создаем поисковую систему
    search = BooleanSearch(INDEX_FILE)

    # Запускаем интерактивный режим
    search.search_interactive()


if __name__ == "__main__":
    main()