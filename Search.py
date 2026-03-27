import json
import os
from PIL import Image

JSON_PATH = r'C:\Users\starm\Desktop\SilentSoft\questions.json'
IMAGE_DIR = r'C:\Users\starm\Desktop\SilentSoft\images'

def show_image(img_name):
    """Открывает картинку, если она существует."""
    if not img_name:
        return
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path):
        try:
            img = Image.open(img_path)
            img.show()
        except Exception as e:
            print(f"[!] Ошибка при открытии картинки {img_name}: {e}")
    else:
        print(f"[!] Файл картинки не найден: {img_name}")


def find_by_id():
    # 1. Загрузка базы
    if not os.path.exists(JSON_PATH):
        print(f"Ошибка: Файл {JSON_PATH} не найден. Сначала запусти парсер!")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # 2. Запрос ID
    try:
        search_id = int(input("Введите ID вопроса для поиска: "))
    except ValueError:
        print("Нужно ввести число (ID).")
        return

    # 3. Поиск вопроса
    target = None
    for q in questions:
        if q['id'] == search_id:
            target = q
            break

    if not target:
        print(f"Вопрос с ID {search_id} не найден в базе.")
        return

    # 4. Вывод данных
    print("\n" + "=" * 50)
    print(f"ИНФОРМАЦИЯ О ВОПРОСЕ №{target['id']}")
    print("=" * 50)
    print(f"ТИП: {target['type']}")
    print(f"ТЕКСТ: {target['question_text']}")

    if target['question_images']:
        print(f"КАРТИНКИ К ВОПРОСУ: {target['question_images']}")
        for img in target['question_images']:
            show_image(img)
    else:
        print("КАРТИНКИ К ВОПРОСУ: Отсутствуют")

    print("\nВАРИАНТЫ ОТВЕТА:")
    if target['options']:
        for idx, opt in enumerate(target['options'], 1):
            img_info = f" [Картинки: {opt['images']}]" if opt['images'] else ""
            print(f"  {idx}. {opt['text']}{img_info}")
            for o_img in opt['images']:
                show_image(o_img)
    else:
        print("  (Вариантов нет, это вопрос с вводом ответа)")

    print("\nПРАВИЛЬНЫЙ ОТВЕТ:")
    print(f"  >> {target['correct_answer']} <<")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    find_by_id()