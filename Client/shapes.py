from tkinter import colorchooser, Button, messagebox, Entry, Label
import tkinter as tk
from typing import Optional, List, Dict, Any
from canvas import DrawingCanvas


class Shapes:
    """
    Класс создания фигур. Используется для создания различных фигур
    в программе для иллюстраций.
    """

    def __init__(self, canvas: DrawingCanvas):
        """
        Конструктор класса фигур.
        """
        self.canvas = canvas
        self.current_shape: Optional[str] = None
        self.shape_color = "black"
        self.fill_color = "white"
        self.line_width = 2  # Толщина линии по умолчанию

        self.drawn_shapes: Dict[int, Any] = {}

    def set_line_width(self, width: int) -> None:
        """Установка толщины линии"""
        self.line_width = width

    def set_shape_color(self, clicked_shape: Optional[int] =None) -> None:
        """
        Этот метод открывает диалог для изменения цвета контура фигуры.
        """
        color_code = colorchooser.askcolor(title="Choose Color")
        if color_code[1]:

            if clicked_shape:
                self.canvas.canvas.itemconfig(clicked_shape, outline=color_code[1])
            else:
                self.shape_color = color_code[1]

    def set_fill_color(self, clicked_shape: Optional[int] = None) -> None:
        """
        Этот метод открывает диалог для изменения цвета заливки фигуры.
        """
        color_code = colorchooser.askcolor(title="Choose Color")
        if color_code[1]:

            if clicked_shape:
                self.canvas.canvas.itemconfig(clicked_shape, fill=color_code[1])

            else:
                self.fill_color = color_code[1]

    def change_specific_oval_rectangle(self, clicked_shape: int, new_width: float, new_height: float,
                                       coords: List[float]) -> None:
        """
        Изменение размеров определённого овала/прямоугольника на холсте.
        """
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2

        new_coords = [center_x - new_width / 2, center_y - new_height / 2,
                      center_x + new_width / 2, center_y + new_height / 2]
        self.canvas.canvas.coords(clicked_shape, new_coords)

    def change_specific_triangle(self, clicked_shape: int, new_width: float, new_height: float,
                                 coords: List[float]) -> None:
        """
        Изменение размеров определённого треугольника на холсте.
        """
        center_x = sum(coords[::2]) / 3
        center_y = sum(coords[1::2]) / 3

        vertex1 = (center_x, center_y - 2 * new_height / 3)
        vertex2 = (center_x - new_width / 2, center_y + new_height / 3)
        vertex3 = (center_x + new_width / 2, center_y + new_height / 3)

        new_coords = [coord for vertex in [vertex1, vertex2, vertex3] for coord in vertex]
        self.canvas.canvas.coords(clicked_shape, *new_coords)

    def change_specific_line(self, clicked_shape: int, new_length: float, new_thickness: float,
                             coords: List[float]) -> None:
        """
        Изменение длины и толщины определённой линии на холсте.
        """
        import math
        x1, y1, x2, y2 = coords
        angle = math.atan2(y2 - y1, x2 - x1)
        x2_new = x1 + new_length * math.cos(angle)
        y2_new = y1 + new_length * math.sin(angle)
        self.canvas.canvas.coords(clicked_shape, x1, y1, x2_new, y2_new)
        self.canvas.canvas.itemconfig(clicked_shape, width=new_thickness)

    def set_shape_size(self, shape_type: str, clicked_shape: Optional[int] = None) -> None:
        """
        Открытие диалога для изменения ширины и высоты (для фигур)
        или длины и толщины (для линий).
        """

        def update_shape_size(event=None) -> None:
            width_height_str = entry.get()
            try:
                width_str, height_str = map(str.strip, width_height_str.split(','))
                first_value = int(width_str)
                second_value = int(height_str)
            except ValueError:
                messagebox.showerror("Неверный ввод", "Введите два целых числа, разделённых запятой.")
                return

            if clicked_shape:
                coords = self.canvas.canvas.coords(clicked_shape)

                if shape_type == "line":
                    # Ограничения для линии
                    if not (1 <= second_value <= 10):
                        messagebox.showerror("Неверная толщина", "Толщина линии должна быть от 1 до 10.")
                        return
                    if first_value < 10 or first_value > 3000:
                        messagebox.showerror("Неверная длина", "Длина линии должна быть от 1 до 3000.")
                        return

                    self.change_specific_line(clicked_shape, first_value, second_value, coords)

                else:
                    # Ограничения для фигур
                    if not (10 <= first_value <= 3000) or not (10 <= second_value <= 3000):
                        messagebox.showerror("Неверный размер", "Ширина и высота должны быть от 10 до 3000.")
                        return

                    if len(coords) == 4:
                        self.change_specific_oval_rectangle(clicked_shape, first_value, second_value, coords)

                    elif len(coords) == 6:
                        self.change_specific_triangle(clicked_shape, first_value, second_value, coords)

            size_dialog.destroy()

        size_dialog = tk.Toplevel()
        size_dialog.title("Изменение размеров фигуры")

        coords = self.canvas.canvas.coords(clicked_shape)

        if shape_type == "line":
            x1, y1, x2, y2 = coords
            current_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            current_thickness = self.canvas.canvas.itemcget(clicked_shape, "width")
            entry_hint = "Введите длину и толщину, разделённые запятой (пример: 150,3)"
            current_values = f"{int(current_length)},{int(float(current_thickness))}"

        else:
            if len(coords) == 4:
                width = abs(coords[2] - coords[0])
                height = abs(coords[3] - coords[1])
            elif len(coords) == 6:
                width = max(coords[::2]) - min(coords[::2])
                height = max(coords[1::2]) - min(coords[1::2])
            else:
                width = height = 0

            entry_hint = "Введите ширину и высоту, разделённые запятой (пример: 100,200)"
            current_values = f"{int(width)},{int(height)}"

        hint_label = Label(size_dialog, text=entry_hint)
        hint_label.pack(padx=10, pady=(10, 5))

        current_label = Label(size_dialog, text=f"Текущие: {current_values}")
        current_label.pack(padx=10, pady=(0, 5))

        entry = Entry(size_dialog, width=30)
        entry.pack(padx=10, pady=5)
        entry.focus_set()  # Фокус сразу на поле ввода

        entry.bind("<Return>", update_shape_size)

        ok_button = Button(size_dialog, text="OK", command=update_shape_size)
        ok_button.pack(padx=10, pady=10)

    def draw_shape_by_drag(self, shape_type: str) -> None:
        """Режим рисования фигур перетаскиванием (линия, прямоугольник, эллипс, треугольник)."""
        self.dragged_shape_name = shape_type
        self.canvas.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event) -> None:
        """Начало рисования фигуры"""
        self.start_x = event.x
        self.start_y = event.y

        if self.dragged_shape_name == "triangle":
            self.dragged_shape = self.canvas.canvas.create_polygon(
                self.start_x, self.start_y,
                self.start_x + 1, self.start_y + 1,
                self.start_x - 1, self.start_y + 1,
                fill=self.fill_color, outline=self.shape_color,
                tags=("movable", "erasable", "shape"))
        elif self.dragged_shape_name == "line":
            self.dragged_shape = self.canvas.canvas.create_line(
                self.start_x, self.start_y,
                self.start_x, self.start_y,
                fill=self.shape_color, width=self.line_width,
                tags=("movable", "erasable", "shape"))
        else:  # Для прямоугольника и эллипса
            self.dragged_shape = getattr(self.canvas.canvas, f"create_{self.dragged_shape_name}")(
                self.start_x, self.start_y, self.start_x, self.start_y,
                fill=self.fill_color, outline=self.shape_color,
                tags=("movable", "erasable", "shape"))

    def on_drag(self, event) -> None:
        """Обновление фигуры при перетаскивании"""
        if not self.dragged_shape:
            return

        if self.dragged_shape_name == "triangle":
            width = event.x - self.start_x
            height = event.y - self.start_y
            top = (self.start_x, self.start_y)
            bottom_right = (self.start_x + width, self.start_y + height)
            bottom_left = (self.start_x - width, self.start_y + height)
            self.canvas.canvas.coords(self.dragged_shape, *top, *bottom_right, *bottom_left)

        elif self.dragged_shape_name == "line":
            self.canvas.canvas.coords(
                self.dragged_shape,
                self.start_x, self.start_y, event.x, event.y)

        else:  # Для прямоугольника и эллипса
            self.canvas.canvas.coords(
                self.dragged_shape,
                self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event) -> None:
        """Завершение рисования фигуры"""
        if self.dragged_shape:
            self.drawn_shapes[self.dragged_shape] = {
                'type': self.dragged_shape_name,
                'object': self.dragged_shape
            }
        self.dragged_shape = None