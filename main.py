from canvas import DrawingCanvas
from shapes import Shapes
from text_box import TextBox
from file_manager import FileManager
from object_manipulator import ObjectManipulator
import tkinter as tk
from tkinter import messagebox
from network_client import NetworkClient
from localization import LocalizationManager
from logger import logger
from utils import resource_path


BUTTONS_BG = 'white'
FRAME_BG = 'light blue'


class MainWindow(tk.Tk):
    def __init__(self, loc: LocalizationManager):
        super().__init__()
        self.iconbitmap(resource_path("Images/icon.ico"))
        self.network = NetworkClient()
        self.loc = loc
        self.loc.register(self)
        logger.info("Приложение запущено")
        self.title('Сетевое приложение "Интерактивный графический редактор"')
        self.geometry("1000x600")
        self.tooltip_window = None
        self.active_button = None

        # Создаем кнопку подключения ДО вызова connect_to_server
        self.modes_frame = tk.Frame(self, background=FRAME_BG)
        self.modes_frame.pack(side="top", fill=tk.BOTH, expand=False)
        self.buttons_frame = tk.Frame(self.modes_frame, bg=FRAME_BG)
        self.buttons_frame.pack(anchor='center')

        self.network_button = tk.Button(self.buttons_frame, text="Подключиться",
                                        command=self.connect_to_server, bg=BUTTONS_BG)
        self.network_button.pack(side="left", padx=(0, 5))

        # Инициализация сетевого подключения
        self.network = NetworkClient()

        # Остальная инициализация
        self.drawing_canvas = DrawingCanvas(self, self.loc, width=800, height=600)
        self.file_manager = FileManager(self.drawing_canvas, self.loc)
        self.text_box = TextBox(self.drawing_canvas, self.loc)
        self.shapes = Shapes(self.drawing_canvas, self.loc)
        self.object_manipulator = ObjectManipulator(self.drawing_canvas, self.text_box, self.shapes, self.loc)

        self.tools_widgets()
        self.buttons_widgets()

        # Обновляем состояние холста при изменениях
        self.drawing_canvas.canvas.bind("<Configure>", self.update_canvas_state)
        self.drawing_canvas.canvas.bind("<ButtonRelease-1>", self.update_canvas_state)
        self.drawing_canvas.canvas.bind("<KeyRelease>", self.update_canvas_state)

        # Устанавливаем пустой режим вместо кисти
        self.drawing_canvas.set_mode('none')

    def connect_to_server(self):
        """Подключается к серверу и начинает получать обновления"""
        if self.network.connected:
            logger.info("Отключение от сервера")
            self.network.disconnect()
            self.network_button.config(
                text=self.loc.gettext("connect"),
                bg=BUTTONS_BG
            )
            return

        logger.info("Подключение к серверу")

        self.network = NetworkClient()
        self.network.connect(
            self.handle_network_message,
            self.on_server_connected,
            self.on_server_connection_failed
        )

    def on_server_connection_failed(self, error):
        self.after(0, lambda: messagebox.showerror(
            self.loc.gettext("connection_error"),
            self.loc.gettext("server_not_running")
        ))

    def on_server_connected(self):
        self.after(0, self._update_ui_connected)

    def _update_ui_connected(self):
        logger.info("Успешное подключение к серверу")
        self.network_button.config(
            text=self.loc.gettext("disconnect"),
            bg="light green"
        )

    def update_active_button(self, mode: str):
        """Обновляет активную кнопку в интерфейсе"""
        if self.active_button:
            self.active_button.config(bg=BUTTONS_BG)

        self.active_button = getattr(self, mode + '_button', None)

        if self.active_button:
            self.active_button.config(bg='gray')

    def handle_network_message(self, message):
        """Обрабатывает сообщения от сервера"""
        if not hasattr(self, 'network') or not self.network.connected:
            return

        message_type = message.get('type')

        if message_type == 'init':
            self.load_canvas_state(message['data'])
            # Устанавливаем режим из состояния сервера
            self.drawing_canvas.set_mode(message['data'].get('current_mode', 'none'))

        elif message_type == 'update':
            # Обновляем только рисунки и фон
            self.drawing_canvas.canvas.delete("all")
            self.drawing_canvas.update_background(message['data']['background'])

            for item_data in message['data'].get('drawings', []):
                self.file_manager.create_item(item_data)

        elif message_type == 'clear':
            self.drawing_canvas.reset_canvas(notify=False)
            self.drawing_canvas.set_mode('none')

    def load_canvas_state(self, state):
        """Загружает состояние холста из данных сервера"""
        # Отключаем обработчики событий, чтобы избежать рекурсии
        self.drawing_canvas.clear_bindings()

        # Очищаем холст
        self.drawing_canvas.canvas.delete("all")

        # Устанавливаем фон
        self.drawing_canvas.update_background(state['background'])

        # Восстанавливаем рисунки
        for item_data in state['drawings']:
            self.file_manager.create_item(item_data)

    def update_canvas_state(self, event=None):
        """Отправляет текущее состояние холста на сервер"""
        if hasattr(self, 'network') and self.network.connected:
            self._send_canvas_state()

    def _send_canvas_state(self):
        """Фактическая отправка состояния холста"""
        items_data = self.file_manager.objects_data_collector()

        self.network.send({
            'type': 'draw',
            'data': {
                'drawings': items_data,
                'background': self.drawing_canvas.bg
            }
        })

    def create_button(self, frame, image_path, command, tooltip_text, pack_side="left", pack_padx=(0, 5),
                      image_subsample=8):
        """
        Создание кнопок на основе переданных параметров.
        """
        button_photo = tk.PhotoImage(file=resource_path(image_path)).subsample(image_subsample)
        button = tk.Button(frame, image=button_photo, command=command, bg=BUTTONS_BG)
        button.pack(side=pack_side, padx=pack_padx)
        self.create_tooltip(button, tooltip_text)
        button.image = button_photo
        return button

    def buttons_widgets(self) -> None:
        """
        Создание кнопок для разных режимов программы.
        """
        self.bg_button = self.create_button(self.buttons_frame, "Images/bg_image.png", lambda: self.modes_modifying('bg'),
                                            "tooltip_bg")

        self.fill_button = self.create_button(self.buttons_frame, "Images/fill_image.png",
                                              lambda: self.modes_modifying("fill"),
                                              "tooltip_fill")

        self.line_button = self.create_button(self.buttons_frame, "Images/line_image.png",
                                              lambda: self.modes_modifying("line"),
                                                   "tooltip_line")

        self.rectangle_button = self.create_button(self.buttons_frame, "Images/rectangle_image.png",
                                                   lambda: self.modes_modifying("rectangle"),
                                                          "tooltip_rectangle")

        self.oval_button = self.create_button(self.buttons_frame, "Images/oval_image.png",
                                              lambda: self.modes_modifying("oval"),
                                                     "tooltip_oval")

        self.polygon_button = self.create_button(self.buttons_frame, "Images/triangle_image.png",
                                                  lambda: self.modes_modifying("polygon"),
                                                  "tooltip_polygon")

        self.drag_button = self.create_button(self.buttons_frame, "Images/drag_image.png",
                                              lambda: self.modes_modifying("drag"),
                                              "tooltip_drag")

        self.text_button = self.create_button(self.buttons_frame, "Images/text_image.png",
                                              lambda: self.modes_modifying("text"),
                                              "tooltip_text")

    def tools_widgets(self) -> None:
        """
        Создание панели меню с инструментами для объектов.
        """

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)
        self.file_menu.add_command(label="Новый", command=self.file_manager.reset_canvas_dialog)
        self.file_menu.add_command(label="Сохранить", command=self.file_manager.save_to_file)
        self.file_menu.add_command(label="Загрузить", command=self.file_manager.load_from_file)
        self.file_menu.add_command(label="Экспортировать в JPEG", command=lambda: self.file_manager.export_to_graphic_file("JPEG"))

        self.text_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label="Текст", menu=self.text_menu)
        self.text_menu.add_command(label="Шрифт", command=self.text_box.choose_font_family)
        self.text_menu.add_command(label="Цвет", command=self.text_box.choose_text_color)
        self.text_menu.add_command(label="Размер", command=self.text_box.choose_text_size)

        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0, background="light blue")
        self.menu_bar.add_cascade(label="Настройки", menu=self.settings_menu)

        self.language_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label="Язык", menu=self.language_menu)

        self.language_menu.add_command(
            label="Русский",
            command=lambda: self.loc.set_language("ru")
        )
        self.language_menu.add_command(
            label="Английский",
            command=lambda: self.loc.set_language("en")
        )
        self.language_menu.add_command(
            label="Белорусский",
            command=lambda: self.loc.set_language("by")
        )

    def modes_modifying(self, mode: str) -> None:
        """Метод для переключения режимов с синхронизацией с сервером"""
        self.drawing_canvas.clear_bindings()
        self.object_manipulator.unbind_objects()

        if self.active_button:
            self.active_button.config(bg=BUTTONS_BG)

        if mode in ['line', 'rectangle', 'oval', 'polygon']:
            self.shapes.draw_shape_by_drag(mode)
            self.active_button = getattr(self, mode + '_button')
        elif mode in ['fill', 'none']:
            self.drawing_canvas.set_mode(mode)
            self.active_button = getattr(self, mode + '_button', None)
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

    def create_tooltip(self, widget, text_key: str) -> None:
        """
        Прикрепляет всплывающую подсказку к виджету.
        """

        widget.tooltip_key = text_key

        def on_enter(event):
            text = self.loc.gettext(widget.tooltip_key)
            self.show_tooltip(text, widget)

        def on_leave(event):
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

    def update_language(self):
        logger.info(f"Смена языка на: {self.loc.current_lang}")
        _ = self.loc.gettext

        # Заголовок окна
        self.title(_("app_title"))

        # Кнопка подключения
        self.network_button.config(
            text=_("disconnect") if self.network.connected else _("connect")
        )

        self.menu_bar.delete(0, "end")

        self.menu_bar.add_cascade(label=_("file"), menu=self.file_menu)
        self.menu_bar.add_cascade(label=_("text"), menu=self.text_menu)
        self.menu_bar.add_cascade(label=_("settings"), menu=self.settings_menu)

        # Пункты меню Файл
        self.file_menu.entryconfig(0, label=_("new"))
        self.file_menu.entryconfig(1, label=_("save"))
        self.file_menu.entryconfig(2, label=_("load"))
        self.file_menu.entryconfig(3, label=_("export_jpeg"))

        # Пункты меню Текст
        self.text_menu.entryconfig(0, label=_("font"))
        self.text_menu.entryconfig(1, label=_("color"))
        self.text_menu.entryconfig(2, label=_("size"))

        # Настройки → Язык
        self.settings_menu.entryconfig(0, label=_("language"))

        # Языки
        self.language_menu.entryconfig(0, label=_("ru"))
        self.language_menu.entryconfig(1, label=_("en"))
        self.language_menu.entryconfig(2, label=_("by"))


if __name__ == '__main__':
    loc = LocalizationManager()
    app = MainWindow(loc)
    app.mainloop()