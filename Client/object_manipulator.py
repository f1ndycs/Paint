import tkinter as tk
from tkinter import messagebox
from canvas import DrawingCanvas
from shapes import Shapes
from text_box import TextBox
from file_manager import FileManager
from typing import Dict, Any, Optional
from PIL import Image, ImageTk

MOVABLE_TAG = "movable"


class ObjectManipulator:
    """
    Класс, отвечающий за манипуляции с объектами:
    удаление, перемещение и специальные функции для каждого типа объекта.
    """

    def __init__(self, canvas: DrawingCanvas, text_box: TextBox, shapes: Shapes, images: FileManager) -> None:
        """
        Конструктор класса ObjectManipulator.
        """
        self.canvas = canvas.canvas
        self.drawing_canvas = canvas
        self.text_box = text_box
        self.shapes = shapes
        self.images = images
        self.drag_data: Dict[str, Any] = {"item": None, "x": 0, "y": 0}

        self.grouped_items: Dict[int, Any] = {}
        self.item_to_group: Dict[int, Any] = {}
        self.clipboard: Optional[Any] = None
        self.current_item: Optional[Any] = None

        self.small_menu = tk.Menu(self.canvas, tearoff=0)
        self.small_menu.add_command(label="Удалить", command=self.remove_item)
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
            else:
                getattr(self.canvas, f"tag_{command}")(item)

    def right_click_menu(self, event) -> None:
        """
        Отображение контекстного меню при правом клике по объекту.
        """
        self.small_menu.delete(0, tk.END)
        closest_item = self.canvas.find_closest(event.x, event.y, halo=1)[0]

        if closest_item is not None:
            item_tags = self.canvas.gettags(closest_item)
            bbox = self.canvas.bbox(closest_item)
            item_type = self.canvas.type(closest_item)

            if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                self.current_item = closest_item

                self.small_menu.add_command(label="Удалить", command=self.remove_item)
                self.small_menu.add_command(label="Переместить наверх",
                                            command=lambda: self.raise_or_lower_item(closest_item, 'raise'))
                self.small_menu.add_command(label="Переместить вниз",
                                            command=lambda: self.raise_or_lower_item(closest_item, 'lower'))

                if not "line" in item_tags:
                    self.small_menu.add_command(label="Копировать",
                                                command=lambda: self.copy_object(closest_item, item_type))

                if "shape" in item_tags:
                    self.shape_options_menu(closest_item, item_type)

                    if item_type in ['rectangle', 'oval', 'triangle']:
                        self.small_menu.add_command(label="Изменить цвет контура",
                                                    command=lambda: self.shapes.set_shape_color(closest_item))

                elif "text_box" in item_tags:
                    self.text_options_menu(closest_item)

                elif "image" in item_tags:
                    self.image_options_menu(closest_item)
            else:
                self.background_options_menu()
        else:
            self.background_options_menu()

        self.small_menu.post(event.x_root, event.y_root)

    def text_options_menu(self, closest_item: int) -> None:
        self.small_menu.add_command(label="Жирный", command=lambda: self.text_box.change_text_style(closest_item, 'bold'))
        self.small_menu.add_command(label="Изменить размер текста",
                                    command=lambda: self.text_box.choose_text_size(closest_item))
        self.small_menu.add_command(label="Изменить цвет текста",
                                    command=lambda: self.text_box.choose_text_color(closest_item))
        self.small_menu.add_command(label="Изменить шрифт",
                                    command=lambda: self.text_box.choose_font_family(closest_item))

    def shape_options_menu(self, closest_item: int, item_type: str) -> None:
        self.small_menu.add_command(label="Изменить размер фигуры",
                                    command=lambda: self.shapes.set_shape_size(item_type, closest_item))
        self.small_menu.add_command(label="Изменить цвет заливки", command=lambda: self.shapes.set_fill_color(closest_item))

    def image_options_menu(self, closest_item: int) -> None:
        self.small_menu.add_command(label="Изменить размер изображения",
                                    command=lambda: self.images.image_manipulation(closest_item, 'resize'))
        self.small_menu.add_command(label="Повернуть изображение",
                                    command=lambda: self.images.image_manipulation(closest_item, 'rotate'))
        self.small_menu.add_command(label="Отразить изображение",
                                    command=lambda: self.images.image_manipulation(closest_item, 'mirror'))

    def background_options_menu(self) -> None:
        self.small_menu.add_command(label="Вставить", command=self.paste_object)
        self.small_menu.add_command(label="Изменить фон", command=self.drawing_canvas.change_bg)

    def remove_item(self) -> None:
        """
        Удаление выбранного элемента с холста.
        """
        if self.current_item:
            item_tags = self.canvas.gettags(self.current_item)

            if "line" in item_tags:
                segment_group = self.drawing_canvas.item_to_segment_group.get(self.current_item)
                if segment_group:
                    for segment in segment_group:
                        self.canvas.delete(segment)
                        del self.drawing_canvas.item_to_segment_group[segment]

            self.canvas.delete(self.current_item)

        self.current_item = None

    def on_item_press(self, event) -> None:
        """
        Событие при нажатии на объект — начало перемещения.
        """
        item = self.canvas.find_closest(event.x, event.y)[0]
        item_tags = self.canvas.gettags(item)
        if MOVABLE_TAG in item_tags:

            if 'line' in item_tags:
                segment_group = self.drawing_canvas.item_to_segment_group.get(item)
                if segment_group:
                    self.drag_data["item"] = segment_group

            else:
                if not self.drag_data["item"]:
                    self.drag_data["item"] = item

            self.drag_data["x"], self.drag_data["y"] = event.x, event.y

    def on_item_release(self, event) -> None:
        """
        Событие при отпускании объекта — завершение перемещения.
        """
        self.drag_data["item"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

    def on_item_move(self, event) -> None:
        """
        Событие при перемещении объекта — обновление координат.
        """
        if self.drag_data["item"]:
            index_x = event.x - self.drag_data["x"]
            index_y = event.y - self.drag_data["y"]

            if isinstance(self.drag_data["item"], int):
                self.canvas.move(self.drag_data["item"], index_x, index_y)

            else:
                for segment in self.drag_data["item"]:
                    self.canvas.move(segment, index_x, index_y)

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def copy_object(self, item: int, item_type: str) -> None:
        """
        Копирование объекта и его параметров в буфер обмена.
        """
        if item_type == 'image':
            self.clipboard = {
                'type': 'image',
                'attributes': self.images.uploaded_images[item]}

        else:
            config = self.get_item_config(item, item_type)
            self.clipboard = {
                'type': item_type,
                'config': config,
                'coords': self.canvas.coords(item)}

    def get_item_config(self, item: int, item_type: str) -> Dict[str, Any]:
        """
        Получение словаря с параметрами конфигурации объекта.
        """
        if item_type == 'image':
            config = self.images.uploaded_images[item]

        else:
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
            return

        item_type = self.clipboard.get('type')

        if item_type == "image":
            self.paste_image()

        else:

            adjusted_coords = [coord + 100 for coord in self.clipboard['coords']]
            if item_type in ['line', 'rectangle', 'oval', 'text', 'triangle']:
                getattr(self.canvas, 'create_' + item_type)(*adjusted_coords, **self.clipboard['config'])

    def paste_image(self) -> None:
        """
        Вставка изображения на холст.
        """
        if self.clipboard is not None:
            file_path = self.clipboard["attributes"]['path']
            image_size = self.clipboard["attributes"]['size']
            rotation = self.clipboard["attributes"]['rotation']

            try:
                image = Image.open(file_path)

                if rotation != 0:
                    image = image.rotate(rotation, expand=True)

                image.thumbnail(image_size)
                photo_image = ImageTk.PhotoImage(image)
                image_id = self.canvas.create_image((100, 100), image=photo_image, anchor='center',
                                                    tags=("image", "movable"))
                self.images.uploaded_images[image_id] = {'photo_image': photo_image, 'path': file_path,
                                                         'size': image_size, 'rotation': rotation}

            except Exception as error:
                messagebox.showerror("Ошибка", f"Не удалось вставить изображение. Ошибка: {error}")