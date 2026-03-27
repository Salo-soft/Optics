import json
import os
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


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def run_viewer():
    if not os.path.exists(JSON_PATH):
        print("Файл json не найден!")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    questions.sort(key=lambda x: x['id'])
    total = len(questions)
    idx = 0

    while idx < total:
        clear_screen()
        q = questions[idx]

        print(f"ПРОГРЕСС: {idx + 1} из {total}")
        print("=" * 60)
        # Пометка типа вопроса
        type_label = "СООТВЕТСТВИЕ (n, l, m)" if q['type'] == 'matching' else q['type'].upper()
        print(f"ВОПРОС №{q['id']} [{type_label}]")
        print("-" * 60)
        print(q['question_text'])

        if q['question_images']:
            print(f"\n[Картинки условия: {len(q['question_images'])}]")
            for img in q['question_images']: show_image(img)

        print("\nВАРИАНТЫ:")
        if q['options']:
            for i, opt in enumerate(q['options'], 1):
                print(f"  {i}. {opt['text']}")
        else:
            print("  [Вопрос с ручным вводом]")

        print("-" * 60)
        # Специальный вывод для 98 вопроса
        if q['id'] == 98:
            print("ПРАВИЛЬНОЕ СООТВЕТСТВИЕ:")
            print("  n -> размер электронного облака")
            print("  l -> форму электронного облака")
            print("  m -> ориентацию в пространстве")
        else:
            print(f"ПРАВИЛЬНЫЙ ОТВЕТ: {q['correct_answer']}")
        print("=" * 60)

        cmd = input("\n[Enter] - Дальше | [Q] - Выход: ").strip().lower()
        if cmd == 'q' or cmd == 'й': break
        idx += 1


if __name__ == "__main__":
    run_viewer()