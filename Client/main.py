from canvas import DrawingCanvas
from brush import Brush
from shapes import Shapes
from text_box import TextBox
from file_manager import FileManager
from object_manipulator import ObjectManipulator
import tkinter as tk

BUTTONS_BG = 'white'
FRAME_BG = 'light blue'


class MainWindow(tk.Tk):
    """
    Главный класс окна и основной оператор графической программы для рисования и дизайна.
    Содержит все элементы графического интерфейса (кнопки, меню и т. д.).
    """

    def __init__(self):
        """
        Конструктор главного окна программы для иллюстраций и дизайна.
        Этот класс отвечает за создание виджетов и переключение между режимами.
        """

        super().__init__()
        self.title('Сетевое приложение "Интерактивный графический редактор"')
        self.geometry("1000x600")
        self.tooltip_window = None
        self.active_button = None

        self.modes_frame = tk.Frame(self, background=FRAME_BG)
        self.modes_frame.pack(side="top", fill=tk.BOTH, expand=False)
        self.buttons_frame = tk.Frame(self.modes_frame, bg=FRAME_BG)
        self.buttons_frame.pack(anchor='center')

        self.drawing_canvas = DrawingCanvas(self, width=800, height=600)
        self.brush = Brush()
        self.file_manager = FileManager(self.drawing_canvas)
        self.text_box = TextBox(self.drawing_canvas.canvas)
        self.shapes = Shapes(self.drawing_canvas)
        self.object_manipulator = ObjectManipulator(self.drawing_canvas, self.text_box, self.shapes, self.file_manager)

        self.drawing_canvas.set_brush(self.brush)
        self.tools_widgets()
        self.buttons_widgets()

    def create_button(self, frame, image_path, command, tooltip_text, pack_side="left", pack_padx=(0, 5),
                      image_subsample=8):
        """
        Создание кнопок на основе переданных параметров.
        """
        button_photo = tk.PhotoImage(file=image_path).subsample(image_subsample)
        button = tk.Button(frame, image=button_photo, command=command, bg=BUTTONS_BG)
        button.pack(side=pack_side, padx=pack_padx)
        self.create_tooltip(button, tooltip_text)
        button.image = button_photo
        return button

    def buttons_widgets(self) -> None:
        """
        Создание кнопок для разных режимов программы.
        """
        self.bg_button = self.create_button(self.buttons_frame, "Images//bg_image.png", lambda: self.modes_modifying('bg'),
                                            "Фон \n Нажмите, чтобы изменить фон")

        self.brush_button = self.create_button(self.buttons_frame, "Images//brush_image.png",
                                               lambda: self.modes_modifying("brush"),
                                               "Кисть \n Нажмите для перехода в режим кисти.")

        self.eraser_button = self.create_button(self.buttons_frame, "Images//eraser_image.png",
                                                lambda: self.modes_modifying("eraser"),
                                                "Ластик \n Нажмите для перехода в режим ластика.")

        self.fill_button = self.create_button(self.buttons_frame, "Images//fill_image.png",
                                              lambda: self.modes_modifying("fill"),
                                              "Заливка \n Нажмите, чтобы залить объект цветом.")

        self.line_button = self.create_button(self.buttons_frame, "Images//line_image.png",
                                                   lambda: self.modes_modifying("line"),
                                                   "Линия \n Нажмите левую кнопку мыши и тяните для создания линии нужного размера.")

        self.rectangle_button = self.create_button(self.buttons_frame, "Images//rectangle_image.png",
                                                          lambda: self.modes_modifying("rectangle"),
                                                          "Прямоугольник \n Нажмите левую кнопку мыши и тяните для создания фигуры нужного размера.")

        self.oval_button = self.create_button(self.buttons_frame, "Images//oval_image.png",
                                                     lambda: self.modes_modifying("oval"),
                                                     "Эллипс \n Нажмите левую кнопку мыши и тяните для создания фигуры нужного размера.")

        self.triangle_button = self.create_button(self.buttons_frame, "Images//triangle_image.png",
                                                  lambda: self.modes_modifying("triangle"),
                                                  "Треугольник \n Нажмите левую кнопку мыши и тяните для создания фигуры нужного размера.")

        self.drag_button = self.create_button(self.buttons_frame, "Images//drag_image.png",
                                              lambda: self.modes_modifying("drag"),
                                              "Перемещение \n Нажмите, чтобы перетаскивать объекты на холсте.")

        self.text_button = self.create_button(self.buttons_frame, "Images//text_image.png",
                                              lambda: self.modes_modifying("text"),
                                              "Текст \n Быстрое создание текстового блока.")

    def tools_widgets(self) -> None:
        """
        Создание панели меню с инструментами для объектов.
        """

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый", command=self.file_manager.reset_canvas_dialog)
        file_menu.add_command(label="Сохранить", command=self.file_manager.save_to_file)
        file_menu.add_command(label="Загрузить", command=self.file_manager.load_from_file)
        file_menu.add_command(label="Загрузить изображение", command=self.file_manager.open_image)
        file_menu.add_command(label="Экспортировать в JPEG", command=lambda: self.file_manager.export_to_graphic_file("JPEG"))

        brush_tools_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label="Кисть", menu=brush_tools_menu)
        brush_tools_menu.add_command(label="Цвет", command=self.brush.choose_color)
        brush_tools_menu.add_command(label="Размер", command=self.brush.set_thickness)

        eraser_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label='Ластик', menu=eraser_menu)
        eraser_menu.add_command(label='Размер', command=self.drawing_canvas.change_eraser_size)

        text_box_tools = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label='Текст', menu=text_box_tools)
        text_box_tools.add_command(label='Шрифт', command=self.text_box.choose_font_family)
        text_box_tools.add_command(label='Цвет', command=self.text_box.choose_text_color)
        text_box_tools.add_command(label='Размер', command=self.text_box.choose_text_size)

    def modes_modifying(self, mode: str) -> None:
        """
        Метод, отвечающий за переключение между режимами в программе.
        """
        self.drawing_canvas.clear_bindings()
        self.object_manipulator.unbind_objects()

        if self.active_button:
            self.active_button.config(bg=BUTTONS_BG)

        if mode in ['line', 'rectangle', 'oval', 'triangle']:
            self.shapes.draw_shape_by_drag(mode)
            self.active_button = getattr(self, mode + '_button')


        elif mode in ['brush', 'eraser', 'fill']:
            getattr(self.drawing_canvas, 'set_mode')(mode)
            self.active_button = getattr(self, mode + '_button')


        elif mode == 'drag':
            self.object_manipulator.bind_objects()
            self.active_button = getattr(self, mode + '_button')


        elif mode == 'bg':
            self.drawing_canvas.change_bg()
            self.active_button = getattr(self, mode + '_button')


        elif mode == 'text':
            self.text_box.choose_text()
            self.active_button = getattr(self, mode + '_button')

        if self.active_button:
            self.active_button.config(bg='gray')

    def create_tooltip(self, widget, text: str) -> None:
        """
        Прикрепляет всплывающую подсказку к виджету.
        """

        def on_enter(event, self=self, text=text, widget=widget):
            self.show_tooltip(text, widget)

        def on_leave(event, self=self):
            self.hide_tooltip()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def show_tooltip(self, text: str, widget) -> None:
        """
        Позиционировать всплывающую подсказку вблизи виджета.
        """
        if hasattr(self, 'tooltip_window'):
            self.hide_tooltip()

        self.tooltip_window = tk.Toplevel()
        self.tooltip_window.wm_overrideredirect(True)
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=text, background="light gray", borderwidth=1, relief="solid")
        label.pack()

    def hide_tooltip(self) -> None:
        """
        Закрывать всплывающую подсказку при потере виджетом фокуса мыши.
        """
        if hasattr(self, 'tooltip_window') and self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()