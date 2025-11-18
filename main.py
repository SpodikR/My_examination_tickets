from plyer import filechooser
from functools import partial
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.metrics import dp

# --- KivyMD імпорти ---
from kivymd.uix.button import MDIconButton
from kivymd.uix.tooltip.tooltip import MDTooltip
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel

# ---------------------
import shutil
import json, os

# Визначаємо шлях до кореня програми ОДИН РАЗ, при старті
# Це гарантує, що ми завжди знаємо, де знаходиться корінь, незалежно від CWD.
APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_ROOT_DIR, "data", "exam_tickets_data.json")
IMAGES_DIR = os.path.join(APP_ROOT_DIR, "images")


def load_data():
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Помилка читання JSON з {DATA_PATH}. Повертаємо порожні дані.")
            return {}
    return {}


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def generate_initial_data():
    if not os.path.exists(DATA_PATH):
        initial_data = {}
        for i in range(1, 26):
            ticket_name = f"Білет {i}"
            questions = []
            for j in range(1, 7):
                questions.append(
                    {"text": f"Запитання {j}", "answer_text": "", "answer_image": ""}
                )
            initial_data[ticket_name] = {"questions": questions}
        save_data(initial_data)
        print("Згенеровано початкові 25 білетів.")


class HoverEditButton(ButtonBehavior, Image):
    tooltip_text = StringProperty("Редагувати")
    tooltip_label = ObjectProperty(None, allownone=True)
    is_hovering = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = "images/icon_edit.png"  # Переконайтеся, що цей шлях правильний
        self.size_hint_x = None
        self.width = dp(40)
        self.fit_mode = "contain"
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        if self.collide_point(*pos):
            if not self.is_hovering:
                self.is_hovering = True
                self.on_enter()
        else:
            if self.is_hovering:
                self.is_hovering = False
                self.on_leave()

    def on_enter(self):
        if not self.tooltip_label:
            self.tooltip_label = MDLabel(
                text=self.tooltip_text,
                size_hint=(None, None),
                height=dp(30),
                padding=[dp(10), dp(5)],
                color=(1, 1, 1, 1),
                font_style="Caption",
                halign="center",
                valign="middle",
            )
            self.tooltip_label.bind(texture_size=self.tooltip_label.setter("size"))
            Window.add_widget(self.tooltip_label)
            self.tooltip_label.md_bg_color = (0.1, 0.1, 0.1, 0.8)
            self.update_tooltip_pos()

    def on_leave(self):
        if self.tooltip_label:
            Window.remove_widget(self.tooltip_label)
            self.tooltip_label = None

    def update_tooltip_pos(self):
        if self.tooltip_label:
            self.tooltip_label.pos = (
                self.x + self.width / 2 - self.tooltip_label.width / 2,
                self.top + dp(5),
            )

    def on_pos(self, instance, value):
        self.update_tooltip_pos()

    def on_size(self, instance, value):
        self.update_tooltip_pos()


class EditQuestionScreen(MDScreen):
    ticket_name = StringProperty("")
    question_index = ObjectProperty(None)

    def load_question_data(self):
        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])

        if self.question_index < len(questions):
            q = questions[self.question_index]
            self.ids.question_text_input.text = q.get("text", "")
            self.ids.answer_text_input.text = q.get("answer_text", "")
            image_path_from_data = q.get("answer_image", "")
            self.ids.image_path_input.text = image_path_from_data
        else:
            self.ids.question_text_input.text = f"Запитання {self.question_index + 1}"
            self.ids.answer_text_input.text = ""
            image_path_from_data = ""
            self.ids.image_path_input.text = ""

        self.update_image_preview(image_path_from_data)

    def save_question(self):
        question = self.ids.question_text_input.text.strip()
        answer = self.ids.answer_text_input.text.strip()
        current_image_path_in_input = self.ids.image_path_input.text.strip()
        final_image_path_to_save = ""

        if current_image_path_in_input:
            os.makedirs(IMAGES_DIR, exist_ok=True)  # Використовуємо глобальну IMAGES_DIR

            image_name = os.path.basename(current_image_path_in_input)
            target_local_path_relative = os.path.join("images", image_name)  # Відносний шлях для JSON
            target_local_path_absolute = os.path.join(
                IMAGES_DIR, image_name
            )  # Абсолютний шлях для копіювання

            abs_current_path = os.path.abspath(current_image_path_in_input)

            if os.path.exists(abs_current_path):
                # Перевіряємо, чи файл вже знаходиться у нашій локальній папці 'images'
                if os.path.normpath(abs_current_path) != os.path.normpath(
                    target_local_path_absolute
                ):
                    try:
                        shutil.copy(
                            abs_current_path, target_local_path_absolute
                        )  # Копіюємо до абсолютного шляху
                        final_image_path_to_save = (
                            target_local_path_relative  # Зберігаємо відносний шлях у JSON
                        )
                        print(f"🖼️ Зображення скопійовано до: {final_image_path_to_save}")
                    except Exception as e:
                        print(
                            f"⚠️ Помилка копіювання зображення {abs_current_path} до {target_local_path_absolute}: {e}"
                        )
                        final_image_path_to_save = ""
                else:
                    final_image_path_to_save = target_local_path_relative
                    print(
                        f"🖼️ Зображення вже знаходиться в локальній папці: {final_image_path_to_save}"
                    )
            else:
                print(f"⚠️ Файл за шляхом '{current_image_path_in_input}' не знайдено.")
                final_image_path_to_save = ""

        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])

        while len(questions) <= self.question_index:
            questions.append({"text": "", "answer_text": "", "answer_image": ""})

        questions[self.question_index] = {
            "text": question,
            "answer_text": answer,
            "answer_image": final_image_path_to_save,
        }

        ticket["questions"] = questions
        data[self.ticket_name] = ticket
        save_data(data)
        print(
            f"✅ Запитання {self.question_index + 1} білета '{self.ticket_name}' збережено!"
        )

        self.manager.get_screen("ticket_questions_screen").set_ticket(self.ticket_name)
        self.manager.current = "ticket_questions_screen"

    def update_image_preview(self, path_to_display):
        if not path_to_display:
            self.ids.image_preview.source = ""
            self.ids.image_preview.opacity = 0
            print(f"🚫 Прев'ю зображення очищено. Шлях пустий.")
            self.ids.image_preview.reload()
            return

        # Завжди будуємо абсолютний шлях до файлу на основі APP_ROOT_DIR
        actual_file_path = path_to_display
        if not os.path.isabs(path_to_display):
            actual_file_path = os.path.join(APP_ROOT_DIR, path_to_display)

        actual_file_path = os.path.normpath(actual_file_path)

        print(f"DEBUG: Поточна директорія: {os.getcwd()}")  # Залишаємо для налагодження CWD
        print(f"DEBUG: Шлях для перевірки існування: '{actual_file_path}'")
        print(f"DEBUG: Шлях, що передається в Kivy Image: '{path_to_display}' (оригінал з JSON або filechooser)")


        if (
            "image_preview" in self.ids
            and os.path.exists(actual_file_path)
            and actual_file_path.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".bmp")
            )
        ):
            # Для Kivy Image.source безпечніше використовувати абсолютний шлях,
            # якщо є підозри на проблеми з відносними шляхами та CWD.
            self.ids.image_preview.source = actual_file_path
            self.ids.image_preview.opacity = 1
            print(f"🖼️ Прев'ю зображення оновлено: {actual_file_path} (використано для source)")
        else:
            self.ids.image_preview.source = ""
            self.ids.image_preview.opacity = 0
            print(
                f"🚫 Прев'ю зображення очищено. Шлях '{path_to_display}' (абсолютний: '{actual_file_path}') недійсний або файл не знайдено."
            )

        self.ids.image_preview.reload()

    def open_image_picker(self):
        try:
            path_selection = filechooser.open_file(
                title="Виберіть зображення для відповіді",
                filters=[("Зображення", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp")],
                multiple=False,
            )
            
            # Додайте цей рядок для налагодження CWD ПІСЛЯ filechooser
            print(f"DEBUG: CWD після filechooser: {os.getcwd()}")

            if path_selection and len(path_selection) > 0:
                selected_image_abs_path = path_selection[0]
                self.ids.image_path_input.text = (
                    selected_image_abs_path  # У полі вводу показуємо абсолютний шлях
                )
                self.update_image_preview(
                    selected_image_abs_path
                )  # Оновлюємо прев'ю з абсолютним шляхом
            else:
                print("Вибір зображення скасовано або файл не вибрано.")
        except Exception as e:
            print(f"Помилка при відкритті вибору файлів: {e}")

    def go_back(self):
        self.manager.current = "ticket_questions_screen"

    def on_enter(self, *args):
        self.load_question_data()
        print("🧠 EditQuestionScreen loaded")


class MainScreen(Screen):
    tickets_list_layout = ObjectProperty(None)

    def on_enter(self, *args):
        self.load_tickets()

    def load_tickets(self):
        self.tickets_list_layout.clear_widgets()
        data = load_data()
        if not data:
            generate_initial_data()
            data = load_data()

        for name in sorted(data.keys()):
            self.add_ticket_widget(name)

    def add_ticket_widget(self, name):
        layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=[dp(5), 0],
        )

        btn = MDRaisedButton(
            text=name,
            size_hint_x=0.8,
            on_release=lambda x, n=name: self.view_ticket_questions(n),
        )

        edit_icon = HoverEditButton(tooltip_text="Редагувати")
        edit_icon.bind(on_release=lambda x, n=name: self.edit_ticket_prompt(n))

        layout.add_widget(btn)
        layout.add_widget(edit_icon)
        self.tickets_list_layout.add_widget(layout)

    def view_ticket_questions(self, ticket_name):
        self.manager.get_screen("ticket_questions_screen").set_ticket(ticket_name)
        self.manager.current = "ticket_questions_screen"

    def edit_ticket_prompt(self, ticket_name):
        self.manager.get_screen("edit_ticket_screen").set_ticket(ticket_name)
        self.manager.current = "edit_ticket_screen"


class EditTicketScreen(MDScreen):
    old_name = StringProperty("")

    def set_ticket(self, old_name):
        self.old_name = old_name
        self.ids.new_ticket_name_input.text = old_name

    def save_changes(self):
        new_name = self.ids.new_ticket_name_input.text.strip()
        if not new_name:
            print("Нова назва не може бути пустою!")
            return

        data = load_data()
        if new_name == self.old_name:
            print("Назва не змінена.")
            self.manager.current = "main_screen"
            return

        if new_name in data:
            print("Білет з такою назвою вже існує!")
            return

        data[new_name] = data.pop(self.old_name)
        save_data(data)
        print(f"Білет '{self.old_name}' перейменовано на '{new_name}'.")
        self.manager.get_screen("main_screen").load_tickets()
        self.manager.current = "main_screen"

    def go_back(self):
        self.manager.current = "main_screen"


class AddTicketScreen(MDScreen):
    ticket_name_input = ObjectProperty(None)
    questions_inputs = ObjectProperty(None)

    def on_enter(self, *args):
        self.ids.ticket_name_input.text = ""
        self.questions_inputs.clear_widgets()
        for i in range(6):
            ti = MDTextField(
                hint_text=f"Питання {i+1}", size_hint_y=None, height=dp(40)
            )
            self.questions_inputs.add_widget(ti)

    def save_ticket(self):
        name = self.ids.ticket_name_input.text.strip()
        if not name:
            print("Назва білета не може бути пустою!")
            return

        data = load_data()
        if name in data:
            print("Білет з такою назвою вже існує!")
            return

        questions = []
        for widget in self.questions_inputs.children[::-1]:
            if isinstance(widget, MDTextField):
                text = widget.text.strip()
                questions.append({"text": text, "answer_text": "", "answer_image": ""})

        while len(questions) < 6:
            questions.append(
                {
                    "text": f"Запитання {len(questions) + 1}",
                    "answer_text": "",
                    "answer_image": "",
                }
            )

        data[name] = {"questions": questions}
        save_data(data)
        print(f"Білет '{name}' збережено!")
        self.manager.get_screen("main_screen").load_tickets()
        self.ids.ticket_name_input.text = ""
        self.manager.current = "main_screen"


class TicketQuestionsScreen(Screen):
    ticket_name = StringProperty("")

    def on_enter(self, *args):
        if self.ticket_name:
            self.load_questions()

    def set_ticket(self, ticket_name):
        self.ticket_name = ticket_name
        self.ids.ticket_title.text = f"[b]{ticket_name}[/b]"
        self.load_questions()

    def load_questions(self):
        self.ids.questions_list.clear_widgets()
        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])

        while len(questions) < 6:
            questions.append(
                {
                    "text": f"Запитання {len(questions) + 1}",
                    "answer_text": "",
                    "answer_image": "",
                }
            )

        ticket["questions"] = questions
        data[self.ticket_name] = ticket
        save_data(data)

        for i, q_data in enumerate(questions):
            question_text = q_data.get("text", "")
            answer_text = q_data.get("answer_text", "")
            answer_image = q_data.get("answer_image", "")

            filled = bool(
                question_text.strip() or answer_text.strip() or answer_image.strip()
            )

            q_display_text = (
                question_text
                if question_text.strip()
                else f"Питання {i+1} (не заповнено)"
            )

            btn = MDRaisedButton(
                text=q_display_text,
                size_hint_y=None,
                height=dp(50),
                md_bg_color=(0.2, 0.6, 0.2, 1) if filled else (0.5, 0.5, 0.5, 1),
                on_release=self.make_edit_callback(i),
            )
            self.ids.questions_list.add_widget(btn)

    def make_edit_callback(self, index):
        return lambda x: self.edit_question(index)

    def edit_question(self, index):
        screen = self.manager.get_screen("edit_question_screen")
        screen.ticket_name = self.ticket_name
        screen.question_index = index
        self.manager.current = "edit_question_screen"

    def add_question(self, *args):
        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])
        if len(questions) < 6:
            self.edit_question(len(questions))
        else:
            print("У білеті вже 6 запитань!")


class ExamTicketsApp(MDApp):
    def build(self):
        self.title = "Моя екзаменаційна шпаргалка"
        self.icon = "images/icon_app.png"

        Builder.load_file("examtickets.kv")

        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name="main_screen"))
        self.sm.add_widget(AddTicketScreen(name="add_ticket_screen"))
        self.sm.add_widget(EditTicketScreen(name="edit_ticket_screen"))
        self.sm.add_widget(TicketQuestionsScreen(name="ticket_questions_screen"))

        self.sm.add_widget(EditQuestionScreen(name="edit_question_screen"))

        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Cyan"
        self.theme_cls.theme_style = "Light"

        return self.sm


if __name__ == "__main__":
    generate_initial_data()
    ExamTicketsApp().run()