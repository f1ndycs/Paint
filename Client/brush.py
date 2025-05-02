from tkinter import colorchooser, Scale, Button
import tkinter as tk


class Brush:
    """
    Класс кисти, используется в графическом редакторе для рисования.
    """

    def __init__(self, color: str = 'black', thickness: float = 2.0) -> None:
        """
        Конструктор кисти с заданным цветом и толщиной.
        """
        self.color = color
        self.thickness = thickness

    def choose_color(self) -> None:
        """
        Открывает диалоговое окно для выбора цвета кисти.
        """
        color_code = colorchooser.askcolor(title="Цвет кисти")
        if color_code[1]:
            self.set_color(color_code[1])

    def set_color(self, color: str) -> None:
        """
        Устанавливает новый цвет кисти.
        """
        self.color = color

    def set_thickness(self) -> None:
        """
        Открывает диалоговое окно для установки толщины кисти с помощью ползунка.
        Выбранное значение сохраняется как новая толщина.
        """

        def update_thickness() -> None:
            self.thickness = float(scale.get() / 10)
            thickness_dialog.destroy()

        thickness_dialog = tk.Toplevel()
        thickness_dialog.title("Толщина кисти")

        scale = Scale(thickness_dialog, from_=0, to=100, orient='horizontal',
                      label=f"Текущая толщина: {self.thickness * 10}", length=300)
        scale.pack(padx=10, pady=10)

        ok_button = Button(thickness_dialog, text="OK", command=update_thickness)
        ok_button.pack()