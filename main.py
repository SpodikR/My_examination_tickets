from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput  # Додано для TextInput в AddTicketScreen
from kivy.uix.image import Image  # Додано для Image в EditQuestionScreen

# main.py - Додайте ці імпорти зверху
from kivy.uix.behaviors import ButtonBehavior # Додаємо HoverBehavior
from kivy.uix.label import Label
from kivy.core.window import Window  # Для додавання віджета до вікна

import json, os


DATA_PATH = "data/exam_tickets_data.json"


def load_data():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def generate_initial_data():
    """Генерує початкові 25 білетів з 6 порожніми питаннями, якщо DATA_PATH не існує."""
    if not os.path.exists(DATA_PATH):
        initial_data = {}
        for i in range(1, 26):  # 25 білетів
            ticket_name = f"Білет {i}"
            questions = []
            for j in range(1, 7):  # 6 питань в кожному білеті
                questions.append(
                    {"text": f"Запитання {j}", "answer_text": "", "answer_image": ""}
                )
            initial_data[ticket_name] = {"questions": questions}
        save_data(initial_data)
        print("Згенеровано початкові 25 білетів.")


class EditQuestionScreen(Screen):
    def set_context(self, ticket_name, question_index):
        self.ticket_name = ticket_name
        self.question_index = question_index
        data = load_data()
        ticket = data.get(ticket_name, {})
        questions = ticket.get("questions", [])

        # Перевіряємо, чи існує питання, інакше ініціалізуємо порожніми полями
        if question_index < len(questions):
            q = questions[question_index]
            self.ids.question_input.text = q.get("text", "")
            self.ids.answer_input.text = q.get("answer_text", "")
            self.ids.image_path_input.text = q.get("answer_image", "")
        else:
            self.ids.question_input.text = (
                f"Запитання {question_index + 1}"  # Нове питання за замовчуванням
            )
            self.ids.answer_input.text = ""
            self.ids.image_path_input.text = ""

        self.update_image_preview(self.ids.image_path_input.text)
        self.ids.image_path_input.bind(text=self.update_image_preview_callback)

    def update_image_preview_callback(self, instance, value):
        self.update_image_preview(value)

    def save_question(self):
        question = self.ids.question_input.text.strip()
        answer = self.ids.answer_input.text.strip()
        image_path = self.ids.image_path_input.text.strip()

        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])

        # Розширюємо список питань, якщо потрібно
        while len(questions) <= self.question_index:
            questions.append({"text": "", "answer_text": "", "answer_image": ""})

        questions[self.question_index] = {
            "text": question,
            "answer_text": answer,
            "answer_image": image_path,
        }

        ticket["questions"] = questions
        data[self.ticket_name] = ticket
        save_data(data)
        print(
            f"Запитання {self.question_index + 1} білета '{self.ticket_name}' збережено!"
        )
        self.manager.get_screen("ticket_questions_screen").set_ticket(self.ticket_name)
        self.manager.current = "ticket_questions_screen"

    def update_image_preview(self, path):
        if os.path.exists(path) and path.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".bmp")
        ):
            self.ids.image_preview.source = path
        else:
            self.ids.image_preview.source = ""
        self.ids.image_preview.reload()  # Оновити зображення


class HoverEditButton(ButtonBehavior, Image): # Видалено HoverBehavior
    tooltip_text = StringProperty("Редагувати")
    tooltip_label = ObjectProperty(None, allownone=True)
    
    # Додамо властивості для відстеження стану наведення
    is_hovering = ObjectProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'images/icon_edit.png'
        self.size_hint_x = None
        self.width = 30
        self.keep_ratio = True
        self.allow_stretch = True

        # Прив'язуємо обробники подій миші до вікна, щоб відстежувати наведення
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        # Перевіряємо, чи позиція миші знаходиться над віджетом
        if self.collide_point(*pos):
            if not self.is_hovering:
                self.is_hovering = True
                self.on_enter()
        else:
            if self.is_hovering:
                self.is_hovering = False
                self.on_leave()

    def on_enter(self):
        # Логіка, коли миша заходить на віджет
        if not self.tooltip_label:
            self.tooltip_label = Label(
                text=self.tooltip_text,
                size_hint=(None, None),
                height=30,
                padding=(10, 5),
                background_color=(0.1, 0.1, 0.1, 0.8),
                color=(1, 1, 1, 1),
                font_size='14sp',
                halign='center',
                valign='middle'
            )
            self.tooltip_label.bind(texture_size=self.tooltip_label.setter('size'))
            self.update_tooltip_pos() # Оновлюємо позицію при створенні
            Window.add_widget(self.tooltip_label)

    def on_leave(self):
        # Логіка, коли миша покидає віджет
        if self.tooltip_label:
            Window.remove_widget(self.tooltip_label)
            self.tooltip_label = None

    def update_tooltip_pos(self):
        # Допоміжна функція для оновлення позиції підказки
        if self.tooltip_label:
            self.tooltip_label.pos = (self.x + self.width / 2 - self.tooltip_label.width / 2, self.top + 5)

    def on_pos(self, instance, value):
        # Викликаємо оновлення позиції підказки при зміні позиції іконки
        self.update_tooltip_pos()

    def on_size(self, instance, value):
        # Викликаємо оновлення позиції підказки при зміні розміру іконки
        self.update_tooltip_pos()

class MainScreen(Screen):
    tickets_list_layout = ObjectProperty(None)

    def on_enter(self):
        self.load_tickets()

    def load_tickets(self):
        self.tickets_list_layout.clear_widgets()
        data = load_data()
        if not data:  # Якщо даних немає, генеруємо початкові
            generate_initial_data()
            data = load_data()  # Перезавантажуємо дані після генерації

        for name in sorted(data.keys()):  # Сортуємо білети за назвою
            self.add_ticket_widget(name)

    def add_ticket_widget(self, name):
        layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=50, spacing=10
        )

        btn = Button(text=name, size_hint_x=0.8) # Змінив size_hint_x, щоб звільнити місце для іконки
        btn.bind(on_press=lambda x, n=name: self.view_ticket_questions(n))

        # Створюємо HoverEditButton замість звичайної кнопки
        edit_icon = HoverEditButton(tooltip_text="Редагувати") # Передаємо текст для підказки
        edit_icon.bind(on_release=lambda x, n=name: self.edit_ticket_prompt(n)) # Використовуємо on_release для ButtonBehavior

        layout.add_widget(btn)
        layout.add_widget(edit_icon) # Додаємо іконку
        self.tickets_list_layout.add_widget(layout)

    def view_ticket_questions(self, ticket_name):
        self.manager.get_screen("ticket_questions_screen").set_ticket(ticket_name)
        self.manager.current = "ticket_questions_screen"

    def edit_ticket_prompt(self, ticket_name):
        self.manager.get_screen("edit_ticket_screen").set_ticket(ticket_name)
        self.manager.current = "edit_ticket_screen"


class EditTicketScreen(Screen):
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

        # Перейменування ключа
        data[new_name] = data.pop(self.old_name)
        save_data(data)
        print(f"Білет '{self.old_name}' перейменовано на '{new_name}'.")
        self.manager.get_screen("main_screen").load_tickets()
        self.manager.current = "main_screen"

    def go_back(self):
        self.manager.current = "main_screen"


class AddTicketScreen(Screen):
    ticket_name_input = ObjectProperty(None)
    questions_inputs = ObjectProperty(
        None
    )  # Додаємо ObjectProperty для BoxLayout з питаннями

    def on_enter(self):
        self.questions_inputs.clear_widgets()  # Очищаємо перед заповненням
        for i in range(6):
            ti = TextInput(hint_text=f"Питання {i+1}", size_hint_y=None, height=40)
            self.questions_inputs.add_widget(ti)

    def save_ticket(self):
        name = self.ticket_name_input.text.strip()
        if not name:
            print("Назва білета не може бути пустою!")
            return

        data = load_data()
        if name in data:
            print("Білет з такою назвою вже існує!")
            return

        questions = []
        for widget in self.questions_inputs.children[::-1]:  # reverse to keep order
            if isinstance(widget, TextInput):
                text = widget.text.strip()
                questions.append({"text": text, "answer_text": "", "answer_image": ""})

        # Якщо питань менше 6, заповнюємо порожніми
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
        self.manager.get_screen(
            "main_screen"
        ).load_tickets()  # Оновлюємо список білетів
        self.ticket_name_input.text = ""
        self.manager.current = "main_screen"


class TicketQuestionsScreen(Screen):
    def set_ticket(self, ticket_name):
        self.ticket_name = ticket_name
        self.ids.ticket_title.text = (
            f"[b]{ticket_name}[/b]"  # Оновлюємо заголовок екрану
        )
        self.ids.questions_list.clear_widgets()
        data = load_data()
        ticket = data.get(ticket_name, {})
        questions = ticket.get("questions", [])

        # Забезпечуємо мінімум 6 питань
        while len(questions) < 6:
            questions.append(
                {
                    "text": f"Запитання {len(questions) + 1}",
                    "answer_text": "",
                    "answer_image": "",
                }
            )

        ticket["questions"] = questions  # Оновлюємо дані, якщо додавали порожні питання
        data[ticket_name] = ticket
        save_data(data)

        for i, q_data in enumerate(questions):
            question_text = q_data.get("text", "")
            answer_text = q_data.get("answer_text", "")
            answer_image = q_data.get("answer_image", "")

            # Вважаємо питання заповненим, якщо є текст питання або текст відповіді, або зображення
            filled = bool(
                question_text.strip() or answer_text.strip() or answer_image.strip()
            )

            q_display_text = (
                question_text
                if question_text.strip()
                else f"Питання {i+1} (не заповнено)"
            )

            btn = Button(
                text=q_display_text,
                size_hint_y=None,
                height=50,
                background_color=(0.2, 0.6, 0.2, 1) if filled else (0.5, 0.5, 0.5, 1),
            )
            btn.bind(on_press=self.make_edit_callback(i))
            self.ids.questions_list.add_widget(btn)

        # Додати кнопку "Додати запитання", якщо їх менше 6
        if len(questions) < 6:
            add_btn = Button(
                text="➕ Додати запитання",
                size_hint_y=None,
                height=50,
                background_color=(0.1, 0.5, 0.8, 1),
            )
            add_btn.bind(on_press=self.add_question)
            self.ids.questions_list.add_widget(add_btn)

    def make_edit_callback(self, index):
        return lambda x: self.edit_question(index)

    def edit_question(self, index):
        screen = self.manager.get_screen("edit_question_screen")
        screen.set_context(self.ticket_name, index)
        self.manager.current = "edit_question_screen"

    def add_question(self, *args):
        data = load_data()
        ticket = data.get(self.ticket_name, {})
        questions = ticket.get("questions", [])
        if len(questions) < 6:  # Дозволяємо додати, якщо менше 6
            self.edit_question(len(questions))
        else:
            print("У білеті вже 6 запитань!")


class ExamApp(App):
    def build(self):
        self.title = "Моя екзаменаційна шпаргалка"
        self.icon = "images/icon.png"
        Builder.load_file("examtickets.kv")
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name="main_screen"))
        self.sm.add_widget(AddTicketScreen(name="add_ticket_screen"))
        self.sm.add_widget(EditTicketScreen(name="edit_ticket_screen"))
        self.sm.add_widget(TicketQuestionsScreen(name="ticket_questions_screen"))
        self.sm.add_widget(EditQuestionScreen(name="edit_question_screen"))
        return self.sm


if __name__ == "__main__":
    generate_initial_data()  # Викликаємо функцію для генерації початкових даних
    ExamApp().run()
