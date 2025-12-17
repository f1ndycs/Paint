import tkinter as tk
from canvas import DrawingCanvas
from shapes import Shapes
from text_box import TextBox
from typing import Dict, Any, Optional
from localization import LocalizationManager
from logger import logger

MOVABLE_TAG = "movable"


class ObjectManipulator:
    """
    Класс, отвечающий за манипуляции с объектами:
    удаление, перемещение и специальные функции для каждого типа объекта.
    """

    def __init__(self, canvas: DrawingCanvas, text_box: TextBox, shapes: Shapes, loc: LocalizationManager) -> None:
        """
        Конструктор класса ObjectManipulator.
        """
        self.loc = loc
        _ = self.loc.gettext

        self.canvas = canvas.canvas
        self.drawing_canvas = canvas
        self.text_box = text_box
        self.shapes = shapes
        self.drag_data: Dict[str, Any] = {"item": None, "x": 0, "y": 0}

        self.grouped_items: Dict[int, Any] = {}
        self.item_to_group: Dict[int, Any] = {}
        self.clipboard: Optional[Any] = None
        self.current_item: Optional[Any] = None

        self.small_menu = tk.Menu(self.canvas, tearoff=0)
        self.small_menu.add_command(label=_("delete"), command=self.remove_item)
        self.canvas.bind("<Button-3>", self.right_click_menu)

    def bind_objects(self) -> None:
        """
        Привязка событий к тегу 'movable', чтобы перемещать объекты.
        """
        self.canvas.tag_bind(MOVABLE_TAG, "<ButtonPress-1>", self.on_item_press)
        self.canvas.tag_bind(MOVABLE_TAG, "<ButtonRelease-1>", self.on_item_release)
        self.canvas.tag_bind(MOVABLE_TAG, "<B1-Motion>", self.on_item_move)

    def unbind_objects(self) -> None:
        """
        Отвязка событий после завершения перемещения.
        """
        self.canvas.tag_unbind(MOVABLE_TAG, "<ButtonPress-1>")
        self.canvas.tag_unbind(MOVABLE_TAG, "<ButtonRelease-1>")
        self.canvas.tag_unbind(MOVABLE_TAG, "<B1-Motion>")

    def raise_or_lower_item(self, item: int, command: str) -> None:
        """
        Поднять или опустить выбранный элемент на один уровень вверх или вниз.
        """
        if item:
            if item in self.drawing_canvas.item_to_segment_group:
                group = self.drawing_canvas.item_to_segment_group[item]
                for item in group:
                    getattr(self.canvas, f"tag_{command}")(item)
                    # Отправляем изменения на сервер
                    self._update_canvas_state()
            else:
                getattr(self.canvas, f"tag_{command}")(item)
                # Отправляем изменения на сервер
                self._update_canvas_state()

    def right_click_menu(self, event) -> None:
        """
        Отображение контекстного меню при правом клике по объекту.
        """
        _ = self.loc.gettext
        self.small_menu.delete(0, tk.END)
        items = self.canvas.find_closest(event.x, event.y, halo=1)

        if not items:
            self.background_options_menu()
            self.small_menu.post(event.x_root, event.y_root)
            return

        closest_item = items[0]

        if closest_item is not None:
            item_tags = self.canvas.gettags(closest_item)
            bbox = self.canvas.bbox(closest_item)
            item_type = self.canvas.type(closest_item)

            if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                self.current_item = closest_item

                self.small_menu.add_command(label=_("delete"), command=self.remove_item)
                self.small_menu.add_command(label=_("move_up"),
                                            command=lambda: self.raise_or_lower_item(closest_item, 'raise'))
                self.small_menu.add_command(label=_("move_down"),
                                            command=lambda: self.raise_or_lower_item(closest_item, 'lower'))
                self.small_menu.add_command(label=_("copy"),
                                            command=lambda: self.copy_object(closest_item, item_type))

                if "shape" in item_tags:
                    self.shape_options_menu(closest_item, item_type)

                    if item_type in ['rectangle', 'oval', 'polygon']:
                        self.small_menu.add_command(label=_("outline_color"),
                                                    command=lambda: self.shapes.set_shape_color(closest_item))

                elif "text_box" in item_tags:
                    self.text_options_menu(closest_item)

            else:
                self.background_options_menu()
        else:
            self.background_options_menu()

        self.small_menu.post(event.x_root, event.y_root)

    def text_options_menu(self, closest_item: int) -> None:
        _ = self.loc.gettext
        self.small_menu.add_command(label=_("bold"), command=lambda: self.text_box.change_text_style(closest_item, 'bold'))
        self.small_menu.add_command(label=_("text_size"),
                                    command=lambda: self.text_box.choose_text_size(closest_item))
        self.small_menu.add_command(label=_("text_color"),
                                    command=lambda: self.text_box.choose_text_color(closest_item))
        self.small_menu.add_command(label=_("text_font"),
                                    command=lambda: self.text_box.choose_font_family(closest_item))

    def shape_options_menu(self, closest_item: int, item_type: str) -> None:
        _ = self.loc.gettext
        self.small_menu.add_command(label=_("shape_size"),
                                    command=lambda: self.shapes.set_shape_size(item_type, closest_item))
        self.small_menu.add_command(label=_("fill_color"), command=lambda: self.shapes.set_fill_color(closest_item))

    def background_options_menu(self) -> None:
        _ = self.loc.gettext
        self.small_menu.add_command(label=_("paste"), command=self.paste_object)
        self.small_menu.add_command(label=_("change_bg"), command=self.drawing_canvas.change_bg)

    def remove_item(self) -> None:
        """
        Удаление выбранного элемента с холста.
        """
        if self.current_item:
            logger.info(f"Удалён объект id={self.current_item}")
            self.canvas.delete(self.current_item)
            self._update_canvas_state()

        if self.current_item:
            self.canvas.delete(self.current_item)
            # Отправляем изменения на сервер
            self._update_canvas_state()

        self.current_item = None

    def on_item_press(self, event) -> None:
        """
        Событие при нажатии на объект — начало перемещения.
        """
        item = self.canvas.find_closest(event.x, event.y)[0]
        item_tags = self.canvas.gettags(item)
        if MOVABLE_TAG in item_tags:

            if not self.drag_data["item"]:
                self.drag_data["item"] = item

            self.drag_data["x"], self.drag_data["y"] = event.x, event.y

    def on_item_release(self, event) -> None:
        """
        Событие при отпускании объекта — завершение перемещения.
        """
        logger.info("Объект перемещён")

        self.drag_data["item"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0
        # Отправляем изменения на сервер
        self._update_canvas_state()

    def on_item_move(self, event) -> None:
        """
        Событие при перемещении объекта — обновление координат.
        """
        if self.drag_data["item"]:
            index_x = event.x - self.drag_data["x"]
            index_y = event.y - self.drag_data["y"]

            if isinstance(self.drag_data["item"], int):
                self.canvas.move(self.drag_data["item"], index_x, index_y)

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def copy_object(self, item: int, item_type: str) -> None:
        """
        Копирование объекта и его параметров в буфер обмена.
        """
        logger.info(f"Скопирован объект id={item}, type={item_type}")

        config = self.get_item_config(item, item_type)
        self.clipboard = {
            'type': item_type,
            'config': config,
            'coords': self.canvas.coords(item)}

    def get_item_config(self, item: int, item_type: str) -> Dict[str, Any]:
        """
        Получение словаря с параметрами конфигурации объекта.
        """
        config_options = self.canvas.itemconfig(item)
        if config_options:
            config = {option: self.canvas.itemcget(item, option) for option in config_options if
                        self.canvas.itemcget(item, option)}

            if item_type == 'text':
                config['text'] = self.canvas.itemcget(item, 'text')
                config['font'] = self.canvas.itemcget(item, 'font')

        return config

    def paste_object(self) -> None:
        """
        Вставка скопированного объекта.
        """
        if not self.clipboard:
            logger.warning("Попытка вставки без объекта в буфере")
            return
        logger.info("Объект вставлен из буфера")

        if not self.clipboard:
            return

        item_type = self.clipboard.get('type')

        adjusted_coords = [coord + 100 for coord in self.clipboard['coords']]
        if item_type in ['line', 'rectangle', 'oval', 'text', 'polygon']:
            getattr(self.canvas, 'create_' + item_type)(*adjusted_coords, **self.clipboard['config'])
            # Отправляем изменения на сервер
            self._update_canvas_state()

    def _update_canvas_state(self):
        """Вспомогательный метод для отправки состояния холста"""
        if hasattr(self.drawing_canvas.root, 'network') and self.drawing_canvas.root.network.connected:
            items_data = self.drawing_canvas.root.file_manager.objects_data_collector()
            self.drawing_canvas.root.network.send({
                'type': 'draw',
                'data': {
                    'drawings': items_data,
                    'background': self.drawing_canvas.bg
                }
            })