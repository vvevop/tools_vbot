import pymorphy3

# Инициализируем анализатор один раз при запуске
morph = pymorphy3.MorphAnalyzer()

# Функция для склонения слова в зависимости от числа
def format_time_word(number: int, word_str: str) -> str:
    """Склоняет слово в зависимости от числа (1 минута, 2 минуты, 5 минут)."""
    word = morph.parse(word_str)[0]
    agreed = word.make_agree_with_number(number).word
    return f"{number} {agreed}"
