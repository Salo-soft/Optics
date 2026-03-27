import customtkinter as ctk
import json
import random
import os
import re
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'questions.json')
IMAGE_DIR = os.path.join(BASE_DIR, 'images')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# --- ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ДЛЯ DRAG-AND-DROP ---

class DraggableCloud(ctk.CTkLabel):
    def __init__(self, master, text, original_data, app_instance, **kwargs):
        super().__init__(master, text=text, fg_color="#34495E", corner_radius=10,
                         width=280, height=45, font=("Arial", 13), wraplength=250, **kwargs)
        self.original_text = original_data
        self.app = app_instance  # Прямая ссылка на QuizApp
        self.bind("<ButtonPress-1>", self.on_start)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.home_x = 0
        self.home_y = 0

    def on_start(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.lift()

    def on_drag(self, event):
        x = self.winfo_x() - self.start_x + event.x
        y = self.winfo_y() - self.start_y + event.y
        self.place(x=x, y=y)

    def on_drop(self, event):
        cx = self.winfo_x() + self.winfo_width() // 2
        cy = self.winfo_y() + self.winfo_height() // 2

        found_slot = False
        # Используем прямую ссылку на список слотов в приложении
        for slot in self.app.matching_slots:
            sx, sy = slot.winfo_x(), slot.winfo_y()
            sw, sh = slot.winfo_width(), slot.winfo_height()

            if sx < cx < sx + sw and sy < cy < sy + sh:
                if slot.assigned_cloud and slot.assigned_cloud != self:
                    slot.assigned_cloud.return_home()

                for s in self.app.matching_slots:
                    if s.assigned_cloud == self:
                        s.assigned_cloud = None
                        s.configure(fg_color="#212F3C")

                self.place(x=sx + (sw - self.winfo_width()) // 2, y=sy + (sh - self.winfo_height()) // 2)
                slot.assigned_cloud = self
                slot.configure(fg_color="transparent")
                found_slot = True
                break

        if not found_slot:
            self.return_home()

    def return_home(self):
        self.place(x=self.home_x, y=self.home_y)
        for s in self.app.matching_slots:
            if s.assigned_cloud == self:
                s.assigned_cloud = None
                s.configure(fg_color="#212F3C")


class MatchingSlot(ctk.CTkLabel):
    def __init__(self, master, letter, **kwargs):
        super().__init__(master, text="Бросьте сюда описание", fg_color="#212F3C",
                         width=310, height=50, corner_radius=8,
                         font=("Arial", 11, "italic"), text_color="#566573", **kwargs)
        self.assigned_cloud = None
        self.letter = letter  # n, l или m
class QuizApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SilentSoft Quiz System v3.0")

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 1000, 850
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(900, 750)

        self.questions_data = self.load_data()
        self.is_busy = False

        if not self.questions_data:
            self.error_exit("Файл questions.json не найден!")
            return

        self.show_main_menu()

    def load_data(self):
        if not os.path.exists(JSON_PATH): return []
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def error_exit(self, message):
        ctk.CTkLabel(self, text=message, text_color="red").pack(expand=True)
        ctk.CTkButton(self, text="Закрыть", command=self.quit).pack(pady=20)

    def show_main_menu(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass

        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.menu_frame, text="SILENT SOFT\nQUIZ SYSTEM",
                     font=("Arial", 42, "bold"), justify="center").pack(pady=40)

        ctk.CTkButton(self.menu_frame, text="ТРЕНИРОВКА", font=("Arial", 20, "bold"),
                      width=350, height=70, command=lambda: self.start_quiz("training")).pack(pady=10)

        ctk.CTkButton(self.menu_frame, text="ЭКЗАМЕН", font=("Arial", 20, "bold"),
                      width=350, height=70, fg_color="#D35400", hover_color="#A04000",
                      command=lambda: self.start_quiz("exam")).pack(pady=10)

        ctk.CTkButton(self.menu_frame, text="ПОИСК ПО ID", font=("Arial", 20, "bold"),
                      width=350, height=70, fg_color="#2E86C1", hover_color="#21618C",
                      command=self.start_search_mode).pack(pady=10)

    def start_quiz(self, mode):
        """Настройка новой сессии теста с рандомизацией вариантов."""
        self.mode = mode
        self.current_idx = 0
        self.score = 0
        self.is_busy = False

        # 1. Выбираем 20 случайных вопросов
        self.test_set = random.sample(self.questions_data, min(20, len(self.questions_data)))

        # 2. РАНДОМИЗАЦИЯ ВАРИАНТОВ ВНУТРИ КАЖДОГО ВОПРОСА
        for q in self.test_set:
            if q.get('options') and len(q['options']) > 1:
                # Перемешиваем список вариантов прямо в объекте вопроса
                random.shuffle(q['options'])

        # 3. Запуск интерфейса
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass
        self.setup_quiz_ui()
        self.show_question()

    def start_search_mode(self):
        """Настройка режима поиска с двумя кнопками."""
        self.mode = "search"
        self.setup_quiz_ui()

        # 1. Настройка верхней панели поиска
        for w in self.top_info.winfo_children(): w.destroy()
        ctk.CTkLabel(self.top_info, text="ID: ", font=("Arial", 16)).pack(side="left", padx=10)
        self.search_entry = ctk.CTkEntry(self.top_info, width=100)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        ctk.CTkButton(self.top_info, text="НАЙТИ", width=80, command=self.perform_search).pack(side="left", padx=10)
        ctk.CTkButton(self.top_info, text="В МЕНЮ", width=80, fg_color="gray", command=self.show_main_menu).pack(
            side="right", padx=10)

        # 2. Настройка нижней панели (ДВЕ КНОПКИ)
        for w in self.bottom_bar.winfo_children(): w.destroy()

        # Кнопка проверки (серая по умолчанию)
        self.verify_btn = ctk.CTkButton(self.bottom_bar, text="ПРОВЕРИТЬ",
                                        font=("Arial", 18, "bold"), width=250, height=55,
                                        fg_color="#5D6D7E", hover_color="#34495E",
                                        command=self.handle_verify)
        self.verify_btn.pack(side="left", padx=20, expand=True)

        # Кнопка показа ответа (синяя)
        self.show_ans_btn = ctk.CTkButton(self.bottom_bar, text="ПРАВИЛЬНЫЙ ОТВЕТ",
                                          font=("Arial", 18, "bold"), width=250, height=55,
                                          fg_color="#2E86C1", hover_color="#21618C",
                                          command=lambda: self.show_feedback(True, self.test_set[0]['correct_answer'],
                                                                             is_search=True))
        self.show_ans_btn.pack(side="left", padx=20, expand=True)

        self.q_text.configure(text="Введите ID вопроса в поле выше")

    def perform_search(self):
        """Поиск вопроса по ID с перемешиванием вариантов."""
        search_id = self.search_entry.get().strip()
        if not search_id.isdigit(): return

        # Ищем вопрос в базе
        target = next((q for q in self.questions_data if q['id'] == int(search_id)), None)

        if target:
            # --- ДОБАВЛЯЕМ ПЕРЕМЕШКУ ТУТ ---
            if target.get('options'):
                random.shuffle(target['options'])
            # -------------------------------

            self.test_set = [target]
            self.current_idx = 0
            self.show_question()
            # Сброс кнопки проверки
            try:
                self.verify_btn.configure(text="ПРОВЕРИТЬ", fg_color="#5D6D7E", state="normal")
            except:
                pass
        else:
            # Если не нашли, очищаем экран и пишем ошибку
            for w in self.q_images_container.winfo_children(): w.destroy()
            for w in self.ans_container.winfo_children(): w.destroy()
            self.q_text.configure(text=f"Вопрос с ID {search_id} не найден!")

    def setup_quiz_ui(self):
        """Обновленный интерфейс с поддержкой множества картинок."""
        for w in self.winfo_children():
            try: w.destroy()
            except: pass

        self.top_info = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.top_info.pack(fill="x", padx=20, pady=10)
        self.progress_label = ctk.CTkLabel(self.top_info, text="", font=("Arial", 18))
        self.progress_label.pack(side="left")

        # Основной скролл-контейнер
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Текст вопроса (оставляем его статичным в топе скролла)
        self.q_text = ctk.CTkLabel(self.scroll_frame, text="", wraplength=800,
                                   font=("Arial", 22, "bold"), justify="left")
        self.q_text.pack(pady=20, padx=20, fill="x")

        # СЮДА БУДУТ ДОБАВЛЯТЬСЯ КАРТИНКИ (динамический контейнер)
        self.q_images_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.q_images_container.pack(fill="x")

        self.ans_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.ans_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.bottom_bar = ctk.CTkFrame(self, height=100, fg_color="transparent")
        self.bottom_bar.pack(fill="x", side="bottom", pady=20)

        self.confirm_btn = ctk.CTkButton(self.bottom_bar, text="ПОДТВЕРДИТЬ",
                                        font=("Arial", 20, "bold"), width=300, height=60,
                                        fg_color="green", command=self.handle_confirm)
        self.confirm_btn.pack()
        self.bind("<Configure>", self.update_wrapping)

    def update_wrapping(self, event=None):
        try:
            new_wrap = self.winfo_width() - 150
            self.q_text.configure(wraplength=new_wrap)
        except:
            pass

    def show_question(self):
        """Отображение вопроса со сбросом прокрутки."""
        import re

        # --- ВОТ ЭТА СТРОЧКА ИСПРАВЛЯЕТ СКРОЛЛ ---
        try:
            self.scroll_frame._parent_canvas.yview_moveto(0)
        except:
            pass
            # -----------------------------------------

        # 1. Очистка старых виджетов
        for w in self.ans_container.winfo_children():
            try:
                w.destroy()
            except:
                w.pack_forget()

        for w in self.q_images_container.winfo_children():
            try:
                w.destroy()
            except:
                w.pack_forget()

        if not self.test_set: return
        q = self.test_set[self.current_idx]

        # Заголовок и текст вопроса
        if self.mode != "search":
            mode_n = "ТРЕНИРОВКА" if self.mode == "training" else "ЭКЗАМЕН"
            self.progress_label.configure(text=f"Режим: {mode_n} | Вопрос {self.current_idx + 1}/20")

        # Отрисовка текста (разбивка по [IMG])
        parts = re.split(r'(\[IMG:.*?\])', q['question_text'])
        for part in parts:
            p = part.strip()
            if not p: continue
            if p.startswith("[IMG:"):
                self.set_image(ctk.CTkLabel(self.q_images_container, text=""), p[5:-1], 800, 300)
                self.q_images_container.winfo_children()[-1].pack(pady=5)
            else:
                ctk.CTkLabel(self.q_images_container, text=p, wraplength=self.winfo_width() - 100,
                             font=("Arial", 20, "bold"), justify="left").pack(pady=5, padx=20, fill="x")

        # --- ОТРИСОВКА ВАРИАНТОВ ---
        self.user_var = ctk.StringVar(value="none")

        # А) МНОЖЕСТВЕННЫЙ ВЫБОР (ТОЛЬКО ДЛЯ ID 30)
        if q['type'] == 'multi_choice':
            self.check_vars = []  # Список для хранения переменных галочек
            ctk.CTkLabel(self.ans_container, text="(Выберите НЕСКОЛЬКО вариантов)", font=("Arial", 14, "italic")).pack(
                pady=5)
            for idx, opt in enumerate(q['options'], 1):
                var = ctk.BooleanVar()
                display_text = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                cb = ctk.CTkCheckBox(self.ans_container, text=f"{idx}. {display_text}",
                                     variable=var, font=("Arial", 16), checkbox_width=24, checkbox_height=24)
                cb.pack(anchor="w", pady=5, padx=20)
                self.check_vars.append((var, opt['text']))  # Сохраняем переменную и текст варианта

        # --- ТИП MATCHING (98 ВОПРОС) ---
        elif q['type'] == 'matching':
            # Определяем параметры для разных вопросов
            if q['id'] == 80:
                letters = [('1', 30), ('2', 100), ('3', 170), ('4', 240)]
                canvas_h = 450
            else: # Для 98 и остальных
                letters = [('n', 30), ('l', 110), ('m', 190)]
                canvas_h = 400

            self.dnd_canvas = ctk.CTkFrame(self.ans_container, height=canvas_h, fg_color="#1B2631")
            self.dnd_canvas.pack(fill="x", pady=10, padx=5)

            self.matching_slots = []
            for letter, y_pos in letters:
                ctk.CTkLabel(self.dnd_canvas, text=f"{letter}:", font=("Arial", 22, "bold")).place(x=20, y=y_pos+5)
                slot = MatchingSlot(self.dnd_canvas, letter)
                slot.place(x=70, y=y_pos)
                self.matching_slots.append(slot)

            # Создаем облака
            shuffled_options = q['options'][:]
            random.shuffle(shuffled_options)

            y_cloud = 30
            for opt in shuffled_options:
                txt = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                cloud = DraggableCloud(self.dnd_canvas, txt, opt['text'], self)
                cloud.home_x = 460
                cloud.home_y = y_cloud
                cloud.place(x=cloud.home_x, y=cloud.home_y)
                y_cloud += 75

        # В) ОБЫЧНЫЙ ВЫБОР (РАДИОКНОПКИ)
        elif q['options']:
            wrap_val = self.winfo_width() - 250
            for idx, opt in enumerate(q['options'], 1):
                f = ctk.CTkFrame(self.ans_container, fg_color="transparent");
                f.pack(anchor="w", pady=8, fill="x")
                rb = ctk.CTkRadioButton(f, text="", variable=self.user_var, value=str(idx), width=20);
                rb.pack(side="left", padx=(10, 5))
                display_text = re.sub(r'\[IMG:.*?\]', '', opt['text']).strip()
                lbl = ctk.CTkLabel(f, text=f"{idx}. {display_text}", font=("Arial", 16), wraplength=wrap_val,
                                   justify="left")
                lbl.pack(side="left", padx=5, fill="x")
                lbl.bind("<Button-1>", lambda e, v=str(idx): self.user_var.set(v))
                if opt.get('images'):
                    for o_img in opt['images']:
                        lbl_i = ctk.CTkLabel(self.ans_container, text="");
                        lbl_i.pack(anchor="w", padx=80)
                        self.set_image(lbl_i, o_img, 250, 150)
        else:
            self.input_entry = ctk.CTkEntry(self.ans_container, placeholder_text="Введите ответ...", width=500,
                                            height=45)
            self.input_entry.pack(pady=20)
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

    def handle_confirm(self):
        """Логика подтверждения с защитой от вылета и блокировки."""
        if self.is_busy and self.mode != "search": return

        try:
            q = self.test_set[self.current_idx]

            if self.mode == "search":
                self.show_feedback(True, q['correct_answer'], is_search=True)
                return

            self.is_busy = True
            self.confirm_btn.configure(state="disabled")

            is_correct = self.check_logic(q)
            if is_correct: self.score += 1

            if self.mode == "training":
                self.show_feedback(is_correct, q['correct_answer'])
            else:
                self.after(400, self.unlock_and_next)

        except Exception as e:
            # Если произошла ошибка, разблокируем интерфейс
            print(f"Ошибка в handle_confirm: {e}")
            self.is_busy = False
            self.confirm_btn.configure(state="normal")

    def check_logic(self, q):
        import re

        def clean(s):
            if not s: return ""
            # Убираем [IMG], приводим к нижнему регистру и удаляем ВСЕ пробелы
            s = re.sub(r'\[IMG:.*?\]', '', str(s))
            s = s.lower().strip()
            s = "".join(s.split())
            s = s.replace("–", "-").replace("—", "-").replace(",", ".")
            if s.endswith("."): s = s[:-1]
            return s

        raw_correct = str(q['correct_answer']).strip()
        correct_cleaned = clean(raw_correct)

        # --- ЛОГИКА ДЛЯ МНОЖЕСТВЕННОГО ВЫБОРА (ID 30) ---
        if q['type'] == 'multi_choice' or q['id'] == 30:
            if not hasattr(self, 'check_vars'): return False

            for var, opt_text in self.check_vars:
                is_checked = var.get()  # Стоит ли галочка
                # Проверяем, содержится ли этот вариант в правильном ответе
                should_be_checked = clean(opt_text) in correct_cleaned

                # Если состояние галочки не совпадает с тем, что должно быть - ошибка
                if is_checked != should_be_checked:
                    return False

            # Если дошли до этой точки и не вылетели — значит всё совпало
            # Но проверим, выбрал ли пользователь хоть что-то (на случай пустых ответов)
            any_checked = any(var.get() for var, _ in self.check_vars)
            return any_checked

        # --- ЛОГИКА ДЛЯ СОПОСТАВЛЕНИЯ (ID 98) ---
        if q['type'] == 'matching':
            results = {}
            for slot in self.matching_slots:
                if not slot.assigned_cloud: return False
                results[slot.letter] = slot.assigned_cloud.original_text.lower()

            # Проверка для вопроса №80 (Порядок возрастания интенсивности)
            if q['id'] == 80:
                is_1_ok = "гравитац" in results.get('1', '')
                is_2_ok = "слабо" in results.get('2', '')
                is_3_ok = "электромагн" in results.get('3', '')
                is_4_ok = "сильн" in results.get('4', '')
                return is_1_ok and is_2_ok and is_3_ok and is_4_ok

            # Проверка для вопроса №98 (Квантовые числа)
            elif q['id'] == 98:
                is_n_ok = "размер" in results.get('n', '')
                is_l_ok = "форм" in results.get('l', '')
                is_m_ok = "ориент" in results.get('m', '')
                return is_n_ok and is_l_ok and is_m_ok

            return False
        # --- ЛОГИКА ДЛЯ ОБЫЧНОГО ВЫБОРА (CHOICE) ---
        elif q['options']:
            choice = self.user_var.get()
            if choice == "none": return False

            selected_opt = q['options'][int(choice) - 1]
            opt_text_cleaned = clean(selected_opt.get('text', ""))
            opt_images = [img.lower() for img in selected_opt.get('images', [])]

            # Проверка картинки
            img_match = re.search(r'img_[a-f0-9]+\.png', raw_correct.lower())
            if img_match:
                if img_match.group(0) in opt_images: return True

            # Проверка текста (строгое соответствие очищенных строк)
            return opt_text_cleaned == correct_cleaned

        # --- ЛОГИКА ДЛЯ ВВОДА (INPUT) ---
        else:
            ans_cleaned = clean(self.input_entry.get())
            return ans_cleaned == correct_cleaned and len(ans_cleaned) > 0

    def show_feedback(self, is_correct, correct_text, is_search=False):
        pop = ctk.CTkToplevel(self)
        pop.geometry("600x500")
        pop.title("Результат")
        pop.attributes("-topmost", True)

        if not is_search:
            pop.protocol("WM_DELETE_WINDOW", lambda: [pop.destroy(), self.unlock_and_next()])

        header_txt = "ИНФОРМАЦИЯ ОБ ОТВЕТЕ:" if is_search else ("✅ ПРАВИЛЬНО!" if is_correct else "❌ ОШИБКА!")
        header_color = "white" if is_search else ("green" if is_correct else "red")
        ctk.CTkLabel(pop, text=header_txt, text_color=header_color, font=("Arial", 22, "bold")).pack(pady=20)

        # ПРОВЕРКА: Если ответ содержит картинку (в формате [IMG:...] или просто .png)
        img_match = re.search(r'\[IMG:(.*?)\]', str(correct_text))

        if img_match or str(correct_text).strip().endswith('.png'):
            # Извлекаем чистое имя файла
            img_filename = img_match.group(1) if img_match else correct_text.strip()

            path = os.path.join(IMAGE_DIR, img_filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    ratio = min(500 / img.width, 250 / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=new_size)
                    ctk.CTkLabel(pop, text="Правильный ответ:", font=("Arial", 14)).pack(pady=5)
                    ctk.CTkLabel(pop, image=ctk_img, text="").pack(pady=10)
                except:
                    ctk.CTkLabel(pop, text="Ошибка загрузки изображения").pack()
        else:
            # Обычный текст
            msg_text = correct_text if is_search else (f"Ожидалось:\n\n{correct_text}" if not is_correct else "")
            ctk.CTkLabel(pop, text=msg_text, font=("Arial", 18), wraplength=500).pack(expand=True, padx=20)

        btn_txt = "ЗАКРЫТЬ" if is_search else "ДАЛЕЕ"
        ctk.CTkButton(pop, text=btn_txt, width=200, height=50,
                      command=lambda: [pop.destroy(), self.unlock_and_next() if not is_search else None]).pack(pady=30)

    def unlock_and_next(self):
        """Безопасная разблокировка кнопки."""
        self.is_busy = False
        try:
            if self.confirm_btn.winfo_exists():
                self.confirm_btn.configure(state="normal")
        except:
            pass

        if self.mode == "search": return
        self.current_idx += 1
        if self.current_idx < len(self.test_set):
            self.show_question()
        else:
            self.show_final_results()

    def show_final_results(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except:
                pass
        f = ctk.CTkFrame(self);
        f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="ТЕСТ ЗАВЕРШЕН", font=("Arial", 36, "bold")).pack(pady=30, padx=50)
        res_c = "green" if self.score >= 15 else "orange" if self.score >= 10 else "red"
        ctk.CTkLabel(f, text=f"Ваш результат: {self.score} / 20", font=("Arial", 28), text_color=res_c).pack(pady=10)
        ctk.CTkButton(f, text="В МЕНЮ", width=250, height=60, command=self.show_main_menu).pack(pady=40)

    def handle_verify(self):
        """Логика кнопки 'ПРОВЕРИТЬ' в режиме поиска."""
        # Сбрасываем флаг занятости для поиска, чтобы кнопка всегда была активна
        self.is_busy = False

        if not self.test_set: return

        q = self.test_set[0]
        is_correct = self.check_logic(q)

        if is_correct:
            self.verify_btn.configure(text="ПРАВИЛЬНО!", fg_color="#27AE60")
        else:
            self.verify_btn.configure(text="НЕВЕРНО!", fg_color="#C0392B")

        self.after(1000, self.reset_verify_btn)

    def reset_verify_btn(self):
        """Возврат кнопки в исходное состояние."""
        try:
            self.verify_btn.configure(text="ПРОВЕРИТЬ", fg_color="#5D6D7E")
        except:
            pass


if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()