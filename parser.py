import os
import json
from docx import Document
import uuid
import hashlib  # Для создания уникальных хешей картинок
from docx.oxml.ns import qn

DOCX_PATH = r'C:\Users\starm\Desktop\SilentSoft\questions.docx'
IMAGE_DIR = r'C:\Users\starm\Desktop\SilentSoft\images'
OUTPUT_JSON = r'C:\Users\starm\Desktop\SilentSoft\questions.json'

# КАРТЫ СИМВОЛОВ (Верхние и Нижние индексы)
SUP_MAP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻',
           '+': '⁺'}
SUB_MAP = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '+': '₊',
           '-': '₋'}

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)


def get_formatted_text_with_anchors(paragraph, doc):
    """Извлекает текст и оборачивает индексы/формулы в тег [MATH:...]."""
    full_content = ""

    for child in paragraph._element.iterchildren():
        if child.tag == qn('w:r'):
            # Проверка картинки
            from docx.text.run import Run
            run_obj = Run(child, paragraph)
            img_name = get_image_from_run(run_obj, doc)
            if img_name:
                full_content += f" [IMG:{img_name}] "

            # Проверка индексов
            is_math = False
            rPr = child.find(qn('w:rPr'))
            if rPr is not None:
                vert = rPr.find(qn('w:vertAlign'))
                if vert is not None:
                    is_math = True # Это либо sup, либо sub

            for t_node in child.findall(qn('w:t')):
                if t_node.text:
                    text_part = t_node.text
                    if is_math:
                        # Оборачиваем в тег для смены шрифта в приложении
                        # При этом всё равно конвертируем в Unicode для надежности
                        # (выбираем sup или sub карту)
                        val = vert.get(qn('w:val'))
                        if val == 'superscript':
                            text_part = "".join(SUP_MAP.get(c, c) for c in text_part)
                        else:
                            text_part = "".join(SUB_MAP.get(c, c) for c in text_part)
                        full_content += f"[MATH:{text_part}]"
                    else:
                        full_content += text_part

        elif child.tag == qn('m:oMath'):
            # Все вордовские уравнения — это MATH
            math_text = ""
            for t_node in child.iter(qn('m:t')):
                if t_node.text: math_text += t_node.text
            full_content += f"[MATH:{math_text}]"

    return full_content.strip().replace("={{sub}}", "_______").replace("{{sub}}", "_______")


def get_image_from_run(run, doc):
    """Извлекает картинку и дает ей имя на основе её содержимого (MD5)."""
    xml_str = run._element.xml
    if 'pic:pic' in xml_str:
        try:
            rid_start = xml_str.find('r:embed="') + 9
            rid_end = xml_str.find('"', rid_start)
            rid = xml_str[rid_start:rid_end]
            image_part = doc.part.related_parts[rid]

            image_bytes = image_part.blob
            file_hash = hashlib.md5(image_bytes).hexdigest()
            filename = f"img_{file_hash}.png"

            img_path = os.path.join(IMAGE_DIR, filename)
            if not os.path.exists(img_path):
                with open(img_path, 'wb') as f:
                    f.write(image_bytes)
            return filename
        except:
            return None
    return None


def parse_docx(path):
    doc = Document(path)
    questions = []
    current_q = None
    waiting_for_new_id = True
    collecting_multi_line_answer = False

    for para in doc.paragraphs:
        text = get_formatted_text_with_anchors(para, doc)
        paragraph_images = []
        for run in para.runs:
            img = get_image_from_run(run, doc)
            if img: paragraph_images.append(img)

        raw_text = para.text.strip()
        if raw_text.isdigit() and waiting_for_new_id:
            if current_q: questions.append(current_q)
            current_q = {"id": int(raw_text), "question_text": "", "question_images": [], "options": [],
                         "correct_answer": "", "type": "choice"}
            waiting_for_new_id = False
            collecting_multi_line_answer = False
            continue

        if current_q is None: continue

        if "Правильный ответ" in text:
            ans_part = text.split(":", 1)[1].strip() if ":" in text else ""
            if not ans_part and paragraph_images:
                current_q["correct_answer"] = paragraph_images[0]
            else:
                current_q["correct_answer"] = ans_part
            collecting_multi_line_answer = True
            waiting_for_new_id = True

            # ОПРЕДЕЛЕНИЕ ТИПОВ ПО ID
            if current_q["id"] in [80, 98]:
                current_q["type"] = "matching"
            elif current_q["id"] == 30:
                current_q["type"] = "multi_choice"
            elif not current_q["options"]:
                current_q["type"] = "input"
            else:
                current_q["type"] = "choice"
            continue

        if collecting_multi_line_answer:
            if text:
                current_q["correct_answer"] += f" {text}"
            elif paragraph_images:
                current_q["correct_answer"] = paragraph_images[0]
            continue

        if text or paragraph_images:
            if not current_q["question_text"] and not current_q["question_images"]:
                current_q["question_text"] = text
                current_q["question_images"].extend(paragraph_images)
            else:
                current_q["options"].append({"text": text, "images": paragraph_images})

    if current_q: questions.append(current_q)
    return questions


if __name__ == "__main__":
    try:
        print("Запуск УМНОГО парсера v5.0 (Поддержка индексов + Фикс типов)...")
        data = parse_docx(DOCX_PATH)
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Готово! Теперь ²³²₉₀Th должен распознаваться как Unicode.")
    except Exception as e:
        print(f"Ошибка: {e}")