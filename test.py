import json
import random
import os
import re
from PIL import Image

JSON_PATH = r'C:\Users\starm\Desktop\SilentSoft\questions.json'
IMAGE_DIR = r'C:\Users\starm\Desktop\SilentSoft\images'


def show_image(img_name):
    if not img_name: return
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path):
        try:
            Image.open(img_path).show()
        except:
            pass


def run_test():
    if not os.path.exists(JSON_PATH):
        print("Файл не найден! Запусти parser.py")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        all_q = json.load(f)

    test_q = random.sample(all_q, min(20, len(all_q)))
    score = 0

    for i, q in enumerate(test_q, 1):
        print(f"\nВопрос {i}/20 (ID: {q['id']})")
        print("-" * 50)
        print(q['question_text'])
        for img in q['question_images']: show_image(img)

        # 1. СПЕЦИАЛЬНЫЙ ВОПРОС 98
        if q['id'] == 98:
            print("\nВАРИАНТЫ ФИЗИЧЕСКОГО СМЫСЛА:")
            for idx, opt in enumerate(q['options'], 1):
                print(f"  {idx}. {opt['text']}")
            try:
                n_val = input("\nВведите номер варианта для n: ").strip()
                l_val = input("Введите номер варианта for l: ").strip()
                m_val = input("Введите номер варианта for m: ").strip()

                if not n_val or not l_val or not m_val:
                    print("\n❌ ОШИБКА! Вы не ввели все значения.")
                else:
                    t_n = q['options'][int(n_val) - 1]['text'].lower()
                    t_l = q['options'][int(l_val) - 1]['text'].lower()
                    t_m = q['options'][int(m_val) - 1]['text'].lower()

                    if "размер" in t_n and ("форму" in t_l or "форма" in t_l) and "ориент" in t_m:
                        print("\n✅ ВЕРНО!");
                        score += 1
                    else:
                        print("\n❌ ОШИБКА! Неверное соответствие.");
                        print(f"Правильно: {q['correct_answer']}")
            except:
                print("\n❌ Ошибка ввода.")
            print("=" * 50);
            continue

        # 2. ОБЫЧНЫЕ ВОПРОСЫ
        if q['options']:
            for idx, opt in enumerate(q['options'], 1):
                print(f"  {idx}. {opt['text']}")
                for o_img in opt['images']: show_image(o_img)

            user_input = input("\nВаш ответ (номер или текст): ").strip().lower()
            correct_s = q['correct_answer'].lower().strip()

            is_ok = False
            # ЗАЩИТА: Если нажали просто Enter
            if not user_input:
                is_ok = False
            # Если ввели цифру (номер варианта)
            elif user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(q['options']):
                    opt_text = q['options'][idx]['text'].lower().strip()
                    # Если текст выбранного варианта совпадает с правильным ответом
                    if opt_text == correct_s or opt_text in correct_s:
                        is_ok = True
            # Если ввели текст (минимум 3 символа для исключения случайных совпадений)
            elif len(user_input) >= 3 and user_input in correct_s:
                is_ok = True
            # Прямое совпадение
            elif user_input == correct_s:
                is_ok = True

            if is_ok:
                print("\n✅ ПРАВИЛЬНО!");
                score += 1
            else:
                print(f"\n❌ ОШИБКА! Правильно: {q['correct_answer']}")

        else:
            # Вопрос без вариантов (INPUT)
            user_input = input("\nВведите ответ: ").strip().lower()
            correct_s = q['correct_answer'].lower().strip()
            if user_input and user_input == correct_s:
                print("\n✅ ПРАВИЛЬНО!");
                score += 1
            else:
                print(f"\n❌ ОШИБКА! Правильно: {q['correct_answer']}")

        print("=" * 50)

    print(f"\nТЕСТ ЗАВЕРШЕН! Результат: {score} из {len(test_q)}")


if __name__ == "__main__":
    run_test()