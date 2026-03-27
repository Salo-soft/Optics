import customtkinter as ctk
import json
import random
import os
import re
from PIL import Image

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'questions.json')
IMAGE_DIR = os.path.join(BASE_DIR, 'images')

# Устанавливаем светлую тему
ctk.set_appearance_mode("light")
# Можно оставить синий или выбрать другой (dark-blue, green)
ctk.set_default_color_theme("blue")

# Наш новый цвет фона (из твоего скриншота)
BG_COLOR = "#F0F2F5"
FRAME_COLOR = "#FFFFFF" # Чисто белый для блоков
TEXT_COLOR = "#1A1A1A"  # Почти черный для текста


# --- КЛАССЫ DRAG-AND-DROP ---
class DraggableCloud(ctk.CTkLabel):
    def __init__(self, master, text, original_data, app_instance, **kwargs):
        super().__init__(master, text=text,
                         fg_color="#3B82F6", # Яркий синий для облака
                         text_color="#FFFFFF", # Белый текст в облаке
                         corner_radius=10,
                         width=280, height=45, font=("Arial", 13, "bold"), wraplength=250, **kwargs)
        self.original_text = original_data
        self.app = app_instance
        self.bind("<ButtonPress-1>", self.on_start)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.home_x, self.home_y = 0, 0

    def on_start(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.lift()

    def on_drag(self, event):
        x = self.winfo_x() - self.start_x + event.x
        y = self.winfo_y() - self.start_y + event.y
        self.place(x=x, y=y)

    def on_drop(self, event):
        cx, cy = self.winfo_x() + self.winfo_width() // 2, self.winfo_y() + self.winfo_height() // 2
        found_slot = False
        for slot in self.app.matching_slots:
            sx, sy, sw, sh = slot.winfo_x(), slot.winfo_y(), slot.winfo_width(), slot.winfo_height()
            if sx < cx < sx + sw and sy < cy < sy + sh:
                if slot.assigned_cloud and slot.assigned_cloud != self: slot.assigned_cloud.return_home()
                for s in self.app.matching_slots:
                    if s.assigned_cloud == self:
                        s.assigned_cloud = None
                        s.configure(text="Бросьте сюда", fg_color="#212F3C")
                self.place(x=sx + (sw - self.winfo_width()) // 2, y=sy + (sh - self.winfo_height()) // 2)
                slot.assigned_cloud = self
                slot.configure(fg_color="#212F3C", text="")
                found_slot = True
                break
        if not found_slot: self.return_home()

    def return_home(self):
        self.place(x=self.home_x, y=self.home_y)
        for s in self.app.matching_slots:
            if s.assigned_cloud == self:
                s.assigned_cloud = None
                s.configure(text="Бросьте сюда", fg_color="#212F3C")


class MatchingSlot(ctk.CTkLabel):
    def __init__(self, master, letter, **kwargs):
        super().__init__(master, text="Бросьте сюда",
                         fg_color="#E2E8F0", # Светло-серый слот
                         text_color="#64748B", # Серый текст
                         width=310, height=50, corner_radius=8, **kwargs)
        self.assigned_cloud = None
        self.letter = letter


# --- ПРИЛОЖЕНИЕ ---
class QuizApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SilentSoft Quiz System v4.2")
        self.geometry("1100x900")
        self.minsize(1000, 800)
        self.configure(fg_color=BG_COLOR)
        self.questions_data = self.load_data()
        self.is_busy = False
        self.test_set = []
        self.user_answers = []
        self.show_main_menu()

    def load_data(self):
        if not os.path.exists(JSON_PATH): return []
        with open(JSON_PATH, 'r', encoding='utf-8') as f: return json.load(f)

    def show_main_menu(self):
        self.mode = "menu"
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame, text="SILENT SOFT QUIZ", font=("Arial", 40, "bold")).pack(pady=40)
        ctk.CTkButton(frame, text="ТРЕНИРОВКА", font=("Arial", 20), width=320, height=70,
                      command=lambda: self.start_quiz("training")).pack(pady=10)
        ctk.CTkButton(frame, text="ЭКЗАМЕН", font=("Arial", 20), width=320, height=70, fg_color="#D35400",
                      command=lambda: self.start_quiz("exam")).pack(pady=10)
        ctk.CTkButton(frame, text="ПОИСК ПО ID", font=("Arial", 20), width=320, height=70, fg_color="#2E86C1",
                      command=self.start_search_mode).pack(pady=10)

    def start_quiz(self, mode):
        self.mode = mode
        self.current_idx = 0
        self.score = 0
        self.test_set = random.sample(self.questions_data, min(20, len(self.questions_data)))
        for q in self.test_set:
            if q.get('options'): random.shuffle(q['options'])
        self.user_answers = [None] * len(self.test_set)
        self.setup_quiz_ui()
        self.show_question()

    def start_search_mode(self):
        self.mode = "search"
        self.test_set = []
        self.user_answers = [None]
        self.current_idx = 0
        self.setup_quiz_ui()

        for w in self.top_info.winfo_children(): w.destroy()
        ctk.CTkLabel(self.top_info, text="ID вопроса: ", font=("Arial", 16)).pack(side="left", padx=10)
        self.search_entry = ctk.CTkEntry(self.top_info, width=100);
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        ctk.CTkButton(self.top_info, text="НАЙТИ", width=80, command=self.perform_search).pack(side="left", padx=10)
        ctk.CTkButton(self.top_info, text="В МЕНЮ", width=80, fg_color="gray", command=self.show_main_menu).pack(
            side="right", padx=10)

        for w in self.bottom_bar.winfo_children(): w.destroy()
        self.verify_btn = ctk.CTkButton(self.bottom_bar, text="ПРОВЕРИТЬ", width=250, height=55, fg_color="#5D6D7E",
                                        command=self.handle_verify)
        self.verify_btn.pack(side="left", expand=True, padx=10)
        ctk.CTkButton(self.bottom_bar, text="ОТВЕТ", width=250, height=55, fg_color="#2E86C1",
                      command=lambda: self.show_feedback(True, self.test_set[0]['correct_answer'],
                                                         True) if self.test_set else None).pack(side="left",
                                                                                                expand=True, padx=10)

    def perform_search(self):
        sid = self.search_entry.get().strip()
        if not sid.isdigit(): return
        target = next((q for q in self.questions_data if q['id'] == int(sid)), None)
        if target:
            # Создаем копию, чтобы не перемешивать оригинальную базу
            target_copy = json.loads(json.dumps(target))
            if target_copy.get('options'): random.shuffle(target_copy['options'])
            self.test_set = [target_copy]
            self.user_answers = [None]
            self.current_idx = 0
            self.show_question()
            self.verify_btn.configure(text="ПРОВЕРИТЬ", fg_color="#5D6D7E")
        else:
            self.q_text.configure(text=f"ID {sid} не найден")

    def setup_quiz_ui(self):
        """Создание интерфейса с панелью навигации для Экзамена."""
        # 1. Очищаем всё окно перед отрисовкой
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass

        # --- БЛОК НАВИГАЦИИ (1-20) ---
        # Появляется ТОЛЬКО в режиме Экзамена
        if self.mode == "exam":
            # Белая подложка для кнопок
            self.nav_frame = ctk.CTkFrame(self, height=70, fg_color=FRAME_COLOR, corner_radius=10)
            self.nav_frame.pack(fill="x", padx=20, pady=(10, 5))

            self.nav_buttons = []
            # Создаем кнопки для каждого вопроса в сете
            for i in range(len(self.test_set)):
                btn = ctk.CTkButton(
                    self.nav_frame,
                    text=str(i + 1),
                    width=38,
                    height=38,
                    fg_color="#BDC3C7",  # Светло-серый (не отвечен)
                    text_color=TEXT_COLOR,
                    font=("Arial", 14, "bold"),
                    command=lambda idx=i: self.jump_to_question(idx)
                )
                btn.pack(side="left", padx=4, pady=10)
                self.nav_buttons.append(btn)

        # 2. Верхняя информационная панель (Прогресс и кнопки управления)
        self.top_info = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_info.pack(fill="x", padx=20, pady=5)

        self.progress_label = ctk.CTkLabel(self.top_info, text="", font=("Arial", 16, "bold"), text_color=TEXT_COLOR)
        self.progress_label.pack(side="left")

        # Кнопки в углу панели
        if self.mode == "exam":
            ctk.CTkButton(self.top_info, text="ЗАВЕРШИТЬ ЭКЗАМЕН", fg_color="#C0392B", text_color="white",
                          hover_color="#A93226", command=self.finish_exam_prompt).pack(side="right")
        else:
            # В тренировке и поиске просто кнопка выхода
            ctk.CTkButton(self.top_info, text="В ГЛАВНОЕ МЕНЮ", fg_color="#7F8C8D", text_color="white",
                          command=self.show_main_menu).pack(side="right")

        # 3. Основная скролл-область для вопроса
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=FRAME_COLOR, corner_radius=15)
        self.scroll_frame.pack(padx=20, pady=5, fill="both", expand=True)

        # Контейнеры внутри скролла
        self.q_images_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.q_images_container.pack(fill="x")

        self.ans_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.ans_container.pack(fill="both", expand=True, padx=20, pady=10)

        # 4. Нижняя панель с главной кнопкой
        self.bottom_bar = ctk.CTkFrame(self, height=90, fg_color="transparent")
        self.bottom_bar.pack(fill="x", side="bottom", pady=10)

        if self.mode != "search":
            # --- ЛОГИКА ВНЕШНЕГО ВИДА КНОПКИ ---
            if self.mode == "exam":
                btn_txt = "СЛЕДУЮЩАЯ СТРАНИЦА"
                btn_clr = "#8E44AD"  # Насыщенный фиолетовый
                hvr_clr = "#7D3C98"  # Темно-фиолетовый при наведении
            else:
                btn_txt = "ПОДТВЕРДИТЬ"
                btn_clr = "#27AE60"  # Твой привычный зеленый
                hvr_clr = "#1E8449"

            self.confirm_btn = ctk.CTkButton(
                self.bottom_bar,
                text=btn_txt,
                font=("Arial", 20, "bold"),
                width=350,  # Немного увеличим ширину для длинного текста
                height=60,
                fg_color=btn_clr,
                hover_color=hvr_clr,
                text_color="white",
                command=self.handle_confirm
            )
            self.confirm_btn.pack()

    def jump_to_question(self, index):
        self.save_current_answer()
        self.current_idx = index
        self.show_question()

    def save_current_answer(self):
        if not self.test_set: return
        q = self.test_set[self.current_idx]
        ans = None
        if q['type'] == 'matching':
            if hasattr(self, 'matching_slots'):
                ans = {slot.letter: (slot.assigned_cloud.original_text if slot.assigned_cloud else None) for slot in
                       self.matching_slots}
        elif q['type'] == 'multi_choice' or q['id'] == 30:
            if hasattr(self, 'check_vars'):
                ans = [var.get() for var, text in self.check_vars]
        elif q['options']:
            if hasattr(self, 'user_var'):
                ans = self.user_var.get()
        else:
            if hasattr(self, 'input_entry'):
                ans = self.input_entry.get()

        self.user_answers[self.current_idx] = ans
        if self.mode == "exam": self.update_nav_colors()

    def update_nav_colors(self):
        """Обновляет цвета кнопок навигации с защитой от ошибок."""
        # ПРОВЕРКА: если мы не в экзамене или кнопки еще не созданы — ничего не делаем
        if self.mode != "exam" or not hasattr(self, 'nav_buttons'):
            return

        for i, ans in enumerate(self.user_answers):
            # Проверяем, существует ли еще кнопка (могла быть удалена при смене режима)
            try:
                if i >= len(self.nav_buttons): break
                btn = self.nav_buttons[i]

                if i == self.current_idx:
                    # Текущий вопрос - синий (в светлой теме #3B82F6)
                    btn.configure(fg_color="#3B82F6", border_width=2, border_color="#1A1A1A")
                elif ans is not None and ans != "none" and ans != "" and (not isinstance(ans, list) or any(ans)):
                    # Отвеченный вопрос - зеленый
                    btn.configure(fg_color="#27AE60", border_width=0)
                else:
                    # Пустой вопрос - серый
                    btn.configure(fg_color="#BDC3C7", border_width=0)
            except:
                continue

    def show_question(self):
        if not self.test_set: return
        try:
            self.scroll_frame._parent_canvas.yview_moveto(0)
        except:
            pass

        for w in self.ans_container.winfo_children(): w.destroy()
        for w in self.q_images_container.winfo_children(): w.destroy()

        q = self.test_set[self.current_idx]
        if self.mode == "exam": self.update_nav_colors()

        # Заголовок прогресса
        if self.mode != "search":
            self.progress_label.configure(text=f"Вопрос {self.current_idx + 1}/20", text_color=TEXT_COLOR)

        # 1. ОТРИСОВКА УСЛОВИЯ (с новым цветом текста)
        parts = re.split(r'(\[IMG:.*?\])', q['question_text'])
        for part in parts:
            p = part.strip()
            if not p: continue
            if p.startswith("[IMG:"):
                lbl = ctk.CTkLabel(self.q_images_container, text="")
                lbl.pack(pady=5);
                self.set_image(lbl, p[5:-1], 800, 350)
            else:
                # ДОБАВЛЕН text_color=TEXT_COLOR
                ctk.CTkLabel(self.q_images_container, text=p, wraplength=self.winfo_width() - 150,
                             font=("Arial", 20, "bold"), justify="left", text_color=TEXT_COLOR).pack(pady=5, padx=20,
                                                                                                     fill="x")

        old_ans = self.user_answers[self.current_idx]

        # 2. ТИП MATCHING
        if q['type'] == 'matching':
            if q['id'] == 80:
                letters_config = [('1', 30), ('2', 100), ('3', 170), ('4', 240)]
                canvas_h = 450
            else:
                letters_config = [('n', 30), ('l', 110), ('m', 190)]
                canvas_h = 400

            self.dnd_canvas = ctk.CTkFrame(self.ans_container, height=canvas_h,
                                           fg_color="#F8FAFC", border_width=1, border_color="#E2E8F0")
            self.dnd_canvas.pack(fill="x", pady=10)

            self.matching_slots = []
            for letter, y_pos in letters_config:
                # Текст буквы (n, l, m) теперь темный
                ctk.CTkLabel(self.dnd_canvas, text=f"{letter}:", font=("Arial", 22, "bold"),
                             text_color=TEXT_COLOR).place(x=20, y=y_pos + 5)
                slot = MatchingSlot(self.dnd_canvas, letter)
                slot.place(x=70, y=y_pos)
                self.matching_slots.append(slot)

            self.clouds = []
            for idx, opt in enumerate(q['options']):
                display_txt = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                # Передаем self в облако
                cloud = DraggableCloud(self.dnd_canvas, display_txt, opt['text'], self)
                cloud.home_x, cloud.home_y = 460, 30 + idx * 75

                # Логика восстановления ответа (с фиксированными координатами)
                assigned_letter = None
                if isinstance(old_ans, dict):
                    for letter, text_in_slot in old_ans.items():
                        if text_in_slot == opt['text']:
                            assigned_letter = letter;
                            break

                if assigned_letter:
                    target_y = 30
                    for L, Y in letters_config:
                        if L == assigned_letter: target_y = Y; break
                    cloud.place(x=85, y=target_y + 2)
                    for s in self.matching_slots:
                        if s.letter == assigned_letter: s.assigned_cloud = cloud; s.configure(text="")
                else:
                    cloud.place(x=cloud.home_x, y=cloud.home_y)
                self.clouds.append(cloud)

        # 3. ТИП MULTI_CHOICE
        elif q['type'] == 'multi_choice' or q['id'] == 30:
            self.check_vars = []
            for idx, opt in enumerate(q['options'], 1):
                var = ctk.BooleanVar(value=old_ans[idx - 1] if isinstance(old_ans, list) else False)
                clean_txt = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                # ДОБАВЛЕН text_color=TEXT_COLOR
                cb = ctk.CTkCheckBox(self.ans_container, text=f"{idx}. {clean_txt}",
                                     variable=var, font=("Arial", 16), text_color=TEXT_COLOR)
                cb.pack(anchor="w", pady=7, padx=20);
                self.check_vars.append((var, opt['text']))

        # 4. ТИП CHOICE
        elif q['options']:
            self.user_var = ctk.StringVar(value=old_ans if old_ans else "none")
            for idx, opt in enumerate(q['options'], 1):
                f = ctk.CTkFrame(self.ans_container, fg_color="transparent");
                f.pack(anchor="w", pady=8, fill="x")
                ctk.CTkRadioButton(f, text="", variable=self.user_var, value=str(idx), width=20).pack(side="left",
                                                                                                      padx=10)
                clean_txt = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                # ДОБАВЛЕН text_color=TEXT_COLOR
                lbl = ctk.CTkLabel(f, text=f"{idx}. {clean_txt}", font=("Arial", 16),
                                   wraplength=700, justify="left", text_color=TEXT_COLOR)
                lbl.pack(side="left");
                lbl.bind("<Button-1>", lambda e, v=str(idx): self.user_var.set(v))
                if opt.get('images'):
                    for i in opt['images']:
                        l = ctk.CTkLabel(self.ans_container, text="");
                        l.pack(anchor="w", padx=80);
                        self.set_image(l, i, 250, 150)

        # 5. ТИП INPUT
        else:
            self.input_entry = ctk.CTkEntry(self.ans_container, width=500, height=45)
            self.input_entry.pack(pady=20)
            if old_ans: self.input_entry.insert(0, old_ans)

    def handle_confirm(self):
        self.save_current_answer()
        q = self.test_set[self.current_idx]
        if self.mode == "training":
            is_ok = self.check_logic_static(q, self.user_answers[self.current_idx])
            if is_ok: self.score += 1
            self.show_feedback(is_ok, q['correct_answer'])
        else:
            if self.current_idx < len(self.test_set) - 1:
                self.current_idx += 1
                self.show_question()
            else:
                self.finish_exam_prompt()

    def handle_verify(self):
        if not self.test_set: return
        self.save_current_answer()
        is_ok = self.check_logic_static(self.test_set[0], self.user_answers[0])
        self.verify_btn.configure(text="ПРАВИЛЬНО!" if is_ok else "НЕВЕРНО!", fg_color="green" if is_ok else "red")
        self.after(1000, lambda: self.verify_btn.configure(text="ПРОВЕРИТЬ", fg_color="#5D6D7E"))

    def check_logic_static(self, q, saved_ans):
        if saved_ans is None or saved_ans == "none" or saved_ans == "": return False

        def clean(s):
            s = re.sub(r'\[IMG:.*?\]', '', str(s)).lower().strip()
            s = "".join(s.split()).replace(",", ".").replace("–", "-").replace("—", "-")
            return s[:-1] if s.endswith(".") else s

        correct_raw = str(q['correct_answer']).strip()
        correct_cleaned = clean(correct_raw)

        if q['type'] == 'matching':
            if not isinstance(saved_ans, dict): return False
            res = {k: clean(v) for k, v in saved_ans.items() if v}
            if q['id'] == 80: return "грави" in res.get('1', '') and "слабо" in res.get('2',
                                                                                        '') and "электр" in res.get('3',
                                                                                                                    '') and "сильн" in res.get(
                '4', '')
            return "размер" in res.get('n', '') and "форм" in res.get('l', '') and "ориент" in res.get('m', '')

        if q['type'] == 'multi_choice' or q['id'] == 30:
            if not isinstance(saved_ans, list): return False
            for i, opt in enumerate(q['options']):
                if saved_ans[i] != (clean(opt['text']) in correct_cleaned): return False
            return any(saved_ans)

        if q['options']:
            try:
                opt = q['options'][int(saved_ans) - 1]
                img_match = re.search(r'img_[a-f0-9]+\.png', correct_raw.lower())
                if img_match: return img_match.group(0) in [img.lower() for img in opt.get('images', [])]
                return clean(opt['text']) == correct_cleaned
            except:
                return False
        return clean(saved_ans) == correct_cleaned

    def set_image(self, label, filename, max_w, max_h):
        path = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(path):
            try:
                img = Image.open(path)
                ratio = min(max_w / img.width, max_h / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=new_size)
                label.configure(image=ctk_img)
            except:
                pass

    def update_wrapping(self):
        try:
            for child in self.q_images_container.winfo_children():
                if isinstance(child, ctk.CTkLabel) and not child.cget("image"):
                    child.configure(wraplength=self.winfo_width() - 150)
        except:
            pass

    def show_feedback(self, is_correct, correct_text, is_search=False):
        pop = ctk.CTkToplevel(self);
        pop.geometry("600x500");
        pop.attributes("-topmost", True)
        if not is_search: pop.protocol("WM_DELETE_WINDOW", lambda: [pop.destroy(), self.unlock_and_next()])
        header = "ИНФОРМАЦИЯ" if is_search else ("✅ ВЕРНО!" if is_correct else "❌ ОШИБКА!")
        ctk.CTkLabel(pop, text=header, text_color="green" if is_correct else "red", font=("Arial", 22, "bold")).pack(
            pady=20)
        img_match = re.search(r'img_[a-f0-9]+\.png', str(correct_text).lower())
        if img_match:
            lbl = ctk.CTkLabel(pop, text="");
            lbl.pack(pady=10);
            self.set_image(lbl, img_match.group(0), 500, 300)
        else:
            ctk.CTkLabel(pop, text=f"Правильный ответ:\n{correct_text}", font=("Arial", 16), wraplength=500).pack(
                pady=20)
        ctk.CTkButton(pop, text="ЗАКРЫТЬ" if is_search else "ДАЛЕЕ",
                      command=lambda: [pop.destroy(), self.unlock_and_next() if not is_search else None]).pack(pady=20)

    def unlock_and_next(self):
        self.is_busy = False
        self.current_idx += 1
        if self.current_idx < len(self.test_set):
            self.show_question()
        else:
            self.show_final_results()

    def finish_exam_prompt(self):
        self.save_current_answer()
        pop = ctk.CTkToplevel(self);
        pop.geometry("350x180");
        pop.attributes("-topmost", True)
        ctk.CTkLabel(pop, text="Завершить экзамен?", font=("Arial", 16)).pack(pady=20)
        f = ctk.CTkFrame(pop, fg_color="transparent");
        f.pack()
        ctk.CTkButton(f, text="ДА", width=100, fg_color="#C0392B",
                      command=lambda: [pop.destroy(), self.calculate_exam_results()]).pack(side="left", padx=10)
        ctk.CTkButton(f, text="НЕТ", width=100, command=pop.destroy).pack(side="left", padx=10)

    def calculate_exam_results(self):
        self.score = sum(1 for i, q in enumerate(self.test_set) if self.check_logic_static(q, self.user_answers[i]))
        self.show_final_results()

    def show_final_results(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass
        f = ctk.CTkFrame(self);
        f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="ТЕСТ ЗАВЕРШЕН", font=("Arial", 36, "bold")).pack(pady=30)
        ctk.CTkLabel(f, text=f"Результат: {self.score} / {len(self.test_set)}", font=("Arial", 28)).pack(pady=10)
        ctk.CTkButton(f, text="В МЕНЮ", width=200, height=50, command=self.show_main_menu).pack(pady=40)


if __name__ == "__main__":
    QuizApp().mainloop()