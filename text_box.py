import tkinter as tk
from tkinter import simpledialog, colorchooser, font, messagebox
from typing import Dict, Tuple, List, Optional, Any
from canvas import DrawingCanvas


class TextBox:
    """
    Класс, отвечающий за создание и редактирование текстовых блоков.
    """

    def __init__(self, canvas: DrawingCanvas, index_x: int = 500, index_y: int = 200, text: str = "Text",
                 font: Tuple = ("Helvetica", 14), color: str = "black"):
        """
        Конструктор класса текстового блока.
        """
        self.canvas = canvas
        self.x = index_x
        self.y = index_y
        self.text = text
        self.font = font
        self.color = color

        self.text_styles: Dict[int, Dict[str, bool]] = {}
        self.text_boxes: Dict[int, Dict[str, Any]] = {}

    def update_text(self, new_text: str) -> None:
        """
        Метод обновляет текст, если он уже создан.
        """
        self.text = new_text

    def update_color(self, new_color: str) -> None:
        """
        Метод обновляет цвет текста.
        """
        self.color = new_color

    def choose_text(self) -> None:
        """
        Метод открывает диалог для ввода нового текста.
        """
        new_text = simpledialog.askstring("Создание текста", "Введите текст:", parent=self.canvas.canvas)
        if new_text:
            self.update_text(new_text)
            self.create_text_box()

    def choose_text_color(self, clicked_text: Optional[int] = None) -> None:
        """
        Метод открывает диалог для изменения цвета текста.
        """
        new_color = colorchooser.askcolor(title="Выбор цвета текста")[1]
        if new_color:
            if clicked_text:
                self.canvas.canvas.itemconfig(clicked_text, fill=new_color)
                # Отправляем изменения на сервер
                self._update_canvas_state()
            else:
                self.update_color(new_color)

    def choose_text_size(self, clicked_text: Optional[int] = None) -> None:
        """
        Метод открывает пользовательское окно ввода размера шрифта с проверкой.
        """

        def apply_size():
            try:
                size = int(entry.get())
                if not (1 <= size <= 400):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целое число от 1 до 400.")
                return

            if clicked_text:
                font_attributes = self.text_font_sync(clicked_text)
                font_attributes[1] = size
                self.canvas.canvas.itemconfig(clicked_text, font=tuple(font_attributes))
                # Отправляем изменения на сервер
                self._update_canvas_state()
            else:
                self.font = (self.font[0], size)

            top.destroy()

        top = tk.Toplevel(self.canvas.canvas)
        top.title("Размер текста")
        top.grab_set()  # Блокирует остальные окна

        tk.Label(top, text="Введите размер текста (1–400):").pack(padx=10, pady=5)
        entry = tk.Entry(top)
        entry.pack(padx=10, pady=5)
        entry.insert(0, str(self.font[1] if not clicked_text else self.split_text_font_attributes(clicked_text)[1]))

        tk.Button(top, text="Применить", command=apply_size).pack(pady=10)

    def create_text_box(self) -> None:
        """
        Метод создаёт новый текстовый блок и сохраняет его ID в словаре.
        """
        text_id = self.canvas.canvas.create_text(
            self.x,
            self.y,
            text=self.text,
            font=self.font,
            fill=self.color,
            tags=("movable", "erasable", "text_box"))
        self.text_boxes[text_id] = {"text": self.text, "font": self.font, "fill": self.color}
        self.text_styles[text_id] = {"bold": False}
        # Отправляем изменения на сервер
        self._update_canvas_state()

    def split_text_font_attributes(self, clicked_text: int) -> Tuple[str, Optional[int], Optional[str], Optional[str]]:
        """
        Метод помогает отслеживать атрибуты шрифта текста.
        """
        font_attr_string = self.canvas.canvas.itemcget(clicked_text, "font")
        font_attributes = font_attr_string.split()

        font_name_parts: List[str] = []
        font_size: Optional[int] = None
        font_style_1: Optional[str] = None
        font_style_2: Optional[str]

        for attr in font_attributes:
            if attr.isdigit():
                font_size = attr
                break
            else:
                font_name_parts.append(attr)

        font_name = " ".join(font_name_parts)

        size_index = font_attributes.index(str(font_size))
        styles = font_attributes[size_index + 1:]

        font_style_1 = styles[0] if len(styles) > 0 else None
        font_style_2 = styles[1] if len(styles) > 1 else None

        return font_name, font_size, font_style_1, font_style_2

    def text_font_sync(self, clicked_text: int) -> List[Any]:
        """
        Создаёт список атрибутов шрифта текстового блока.
        """
        font_name, font_size, font_style_1, font_style_2 = self.split_text_font_attributes(clicked_text)
        font_attributes: List[Any] = [font_name, font_size]

        if self.text_styles[clicked_text]["bold"]:
            font_attributes.append("bold")

        return font_attributes

    def change_text_style(self, clicked_text: int, style: str) -> None:
        """
        Метод изменяет стиль текста (например, жирный).
        """
        if clicked_text not in self.text_styles:
            self.text_styles[clicked_text] = {"bold": False}

        self.text_styles[clicked_text][style] = not self.text_styles[clicked_text][style]
        font_attributes = self.text_font_sync(clicked_text)

        self.canvas.canvas.itemconfig(clicked_text, font=tuple(font_attributes))
        # Отправляем изменения на сервер
        self._update_canvas_state()

    def choose_font_family(self, clicked_text: Optional[int] = None) -> None:
        """
        Метод открывает окно с полосой прокрутки для выбора шрифта.
        """
        self.font_window = tk.Toplevel(self.canvas.canvas)
        self.font_window.title("Выбор шрифта")

        self.font_listbox = tk.Listbox(self.font_window)
        self.font_listbox.pack(side="right", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.font_window, orient="vertical", command=self.font_listbox.yview)
        scrollbar.pack(side="top", fill="y")
        self.font_listbox.config(yscrollcommand=scrollbar.set)

        for family in font.families():
            self.font_listbox.insert("end", family)
        self.font_listbox.bind("<<ListboxSelect>>", lambda event: self.update_font(event, clicked_text))

    def update_font(self, event=None, clicked_text: Optional[int] = None) -> None:
        """
        Метод обновляет шрифт текста.
        """
        if not self.font_listbox.curselection():
            return

        selected_font = self.font_listbox.get(self.font_listbox.curselection())
        if clicked_text:
            font_attributes = self.text_font_sync(clicked_text)
            font_attributes[0] = selected_font
            self.canvas.canvas.itemconfig(clicked_text, font=tuple(font_attributes))
            # Отправляем изменения на сервер
            self._update_canvas_state()
        else:
            self.font = selected_font
        self.font_window.destroy()

    def _update_canvas_state(self):
        """Вспомогательный метод для отправки состояния холста"""
        if hasattr(self.canvas.root, 'network') and self.canvas.root.network.connected:
            items_data = self.canvas.root.file_manager.objects_data_collector()
            self.canvas.root.network.send({
                'type': 'draw',
                'data': {
                    'drawings': items_data,
                    'background': self.canvas.bg
                }
            })