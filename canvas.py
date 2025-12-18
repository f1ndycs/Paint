import tkinter as tk
from tkinter import colorchooser
from typing import List, Tuple, Dict
from localization import LocalizationManager
from logger import logger


class DrawingCanvas:
    """
    Класс холста, используемого в графическом редакторе.
    Обрабатывает создание простых линий и стирание объектов.
    """

    def __init__(self, master, loc: LocalizationManager, width: int, height: int, bg: str = "white", mode: str = 'drag') -> None:
        """
        Конструктор объекта холста.
        """
        self.loc = loc
        self.root = master
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg=bg, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bg = bg
        self.width = width
        self.height = height
        self.mode = mode

        self.is_drawing = False
        self.start_x, self.start_y = None, None

        self.current_segment: List[int] = []
        self.item_to_segment_group: Dict[int, List[int]] = {}
        self.current_segment_coord: List[Tuple[int, int]] = []
        self.segment_groups_coord: Dict[int, List[Tuple[int, int]]] = {}

        self.locked = False
        self.lock_client = None

    def get_mode(self) -> str:
        """
        Получение текущего режима рисования (кисть, ластик и т.п.).
        """
        return self.mode

    def change_bg(self) -> None:
        """Открывает диалог выбора цвета фона холста."""
        _ = self.loc.gettext
        new_bg = colorchooser.askcolor(title=_("choose_background_color"))[1]
        if new_bg:
            self.update_background(new_bg)
            logger.info(f"Изменён цвет фона холста: {new_bg}")
            self._update_canvas_state()

    def update_background(self, new_bg: str) -> None:
        """
        Обновляет цвет фона холста.
        """
        self.bg = new_bg
        self.canvas.config(bg=new_bg)

    def clear_bindings(self) -> None:
        """
        Отвязывает события рисования и стирания.
        Используется при переключении режимов.
        """
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")

    def fill_with_color(self, event) -> None:
        """
        Заливка объектов или фона цветом.
        """
        if self.fill_color:
            item = self.canvas.find_closest(event.x, event.y)[0]
            item_tags = self.canvas.gettags(item)

            if 'shape' in item_tags or 'text_box' in item_tags:
                self.canvas.itemconfig(item, fill=self.fill_color)
                logger.info(f"Заливка объекта {item} цветом {self.fill_color}")

            else:
                self.canvas.config(bg=self.fill_color)
                logger.info(f"Заливка фона цветом {self.fill_color}")

        # Отправляем изменения на сервер
        self._update_canvas_state()

    def set_mode(self, mode: str) -> None:
        """"""
        _ = self.loc.gettext
        self.mode = mode

        if mode == 'fill':
            self.fill_color = colorchooser.askcolor(title=_("choose_fill_color"))[1]
            self.canvas.bind("<Button-1>", self.fill_with_color)

    def reset_canvas(self, notify: bool = True) -> None:
        """
        Сброс холста. Удаляет все объекты и сбрасывает состояние.
        """
        self.canvas.delete("all")
        self.canvas.config(bg="white")  # Устанавливаем белый фон
        self.bg = "white"  # Обновляем переменную фона

        logger.info("Холст очищен")

        self.is_drawing = False
        self.start_x, self.start_y = None, None
        self.current_segment = []
        self.item_to_segment_group = {}

        # Отправляем изменения на сервер
        self._update_canvas_state()

    def _update_canvas_state(self):
        """Вспомогательный метод для отправки состояния холста"""
        if hasattr(self.root, 'network') and self.root.network.connected:
            items_data = self.root.file_manager.objects_data_collector()
            self.root.network.send({
                'type': 'draw',
                'data': {
                    'drawings': items_data,
                    'background': self.bg
                }
            })