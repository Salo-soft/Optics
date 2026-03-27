import json
import os
import re

JSON_PATH = r'C:\Users\starm\Desktop\SilentSoft\questions.json'


def strict_clean(s):
    """Та же функция очистки, что и в приложении."""
    if not s: return ""
    s = re.sub(r'\[IMG:.*?\]', '', str(s))
    s = s.lower().strip()
    s = "".join(s.split())
    s = s.replace(",", ".").replace("–", "-").replace("—", "-")
    if s.endswith("."): s = s[:-1]
    return s


def validate_database():
    if not os.path.exists(JSON_PATH):
        print("Файл базы не найден!")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    errors = []
    total = len(questions)

    print(f"Начинаю проверку {total} вопросов...\n")

    for q in questions:
        q_id = q['id']
        correct_raw = str(q['correct_answer']).strip()
        correct_cleaned = strict_clean(correct_raw)

        # 1. Проверка вопросов с вариантами (Choice)
        if q['options']:
            found = False
            # Ищем, совпадает ли правильный ответ хотя бы с одним вариантом
            for opt in q['options']:
                opt_text_cleaned = strict_clean(opt.get('text', ""))
                opt_images = [img.lower() for img in opt.get('images', [])]

                # Проверка по тексту
                if opt_text_cleaned == correct_cleaned:
                    found = True
                    break

                # Проверка по картинке (если ответ - имя файла)
                img_match = re.search(r'img_[a-f0-9]+\.png', correct_raw.lower())
                if img_match and img_match.group(0) in opt_images:
                    found = True
                    break

            if not found:
                errors.append(f"ID {q_id}: Правильный ответ '{correct_raw}' НЕ НАЙДЕН в вариантах.")

        # 2. Проверка на пустые данные
        if not q['question_text'] and not q['question_images']:
            errors.append(f"ID {q_id}: Пустое условие вопроса!")

        if not correct_raw:
            errors.append(f"ID {q_id}: Отсутствует правильный ответ!")

    # ИТОГИ
    print("-" * 50)
    if not errors:
        print("✅ ВСЕ ВОПРОСЫ В ПОРЯДКЕ! База идеальна.")
    else:
        print(f"❌ НАЙДЕНО ОШИБОК: {len(errors)}")
        for err in errors:
            print(f"  - {err}")
    print("-" * 50)


if __name__ == "__main__":
    validate_database()