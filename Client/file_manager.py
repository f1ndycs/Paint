from tkinter.simpledialog import askstring
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
from typing import Tuple, List, Dict, Any, Optional
import json
from canvas import DrawingCanvas


class FileManager:
    """
    Класс менеджера файлов, отвечает за сохранение и загрузку холста и изображений.
    """

    def __init__(self, my_canvas: DrawingCanvas) -> None:
        """
        Конструктор менеджера файлов.
        """
        self.canvas = my_canvas
        self.uploaded_images: Dict[int, Dict[str, Any]] = {}

    def objects_data_collector(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Собирает данные обо всех объектах, размещённых на холсте,
        для последующего восстановления.
        """
        items_data = []
        images_data = []

        for item in self.canvas.canvas.find_all():
            item_tags = self.canvas.canvas.gettags(item)
            item_type = self.canvas.canvas.type(item)
            item_config = self.get_item_config(item, item_type)

            if "image" in item_tags:
                images_data.append({
                    'image_id': item,
                    'path': self.uploaded_images[item]['path'],
                    'coords': self.canvas.canvas.coords(item)})
            else:
                items_data.append({
                    'type': item_type,
                    'coords': self.canvas.canvas.coords(item),
                    'tags': item_tags,
                    'config': item_config})

        return items_data, images_data

    def get_item_config(self, item, item_type):
        """
        Создаёт словарь с конфигурацией (параметрами) объекта.
        """
        config = {option: self.canvas.canvas.itemcget(item, option) for option in self.canvas.canvas.itemconfig(item) if
                  self.canvas.canvas.itemcget(item, option)}
        if item_type == 'text':
            config['text'] = self.canvas.canvas.itemcget(item, 'text')
            config['font'] = self.canvas.canvas.itemcget(item, 'font')

        return config

    def save_to_file(self) -> None:
        """
        Диалог сохранения файла.
        Сохраняет данные холста для продолжения редактирования позже.
        """
        items_data, images_data = self.objects_data_collector()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:

            try:
                with open(file_path, 'w') as file:
                    json.dump({'drawings': items_data, 'images': images_data}, file, indent=4)
                messagebox.showinfo("Успех", "Холст успешно сохранён.")

            except Exception as error:
                messagebox.showerror("Ошибка", f"Не удалось сохранить холст. Ошибка: {error}")

    def load_from_file(self) -> None:
        """
        Загружает данные из файла и создаёт объекты на холсте для редактирования.
        """
        response = messagebox.askokcancel("Подтверждение", "Сохранить текущий холст?")
        if response:
            self.save_to_file()

        else:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if file_path:

                try:
                    with open(file_path, 'r') as file:
                        items_data = json.load(file)
                    self.canvas.canvas.delete("all")

                    for item_data in items_data.get('drawings', []):
                        self.create_item(item_data)
                    for image_data in items_data.get('images', []):
                        self.open_image(image_data['path'], image_data['coords'])

                except Exception as error:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить данные холста. Ошибка: {error}")

    def create_item(self, item_data: Dict[str, Any]) -> None:
        """
        Создаёт объект из данных, загруженных из файла.
        """
        item_type = item_data['type']
        coords = item_data['coords']
        tags = tuple(item_data['tags'])
        config = item_data['config']
        config.pop('tags', None)

        if item_type == "image":
            self.open_image(item_data['path'], coords)

        else:
            if item_type in ['line', 'rectangle', 'oval', 'text', 'triangle']:
                getattr(self.canvas.canvas, 'create_' + item_type)(coords, **config, tags=tags)

    def open_image(self, file_path: Optional[str] = None, coords: Optional[Tuple[int, int]] = None) -> None:
        """
        Загружает изображение на холст.
        Если путь не указан — открывает диалог выбора файла.
        """
        if coords is None:
            coords = (200, 200)
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])

        if file_path:
            image = Image.open(file_path)
            original_size = image.size
            max_size = (400, 400)
            image.thumbnail(max_size, Image.LANCZOS)  # сохраняем пропорции
            photo_image = ImageTk.PhotoImage(image)

            image_id = self.canvas.canvas.create_image(*coords, image=photo_image, anchor='center',
                                                       tags=("image", "movable"))
            self.uploaded_images[image_id] = {
                'photo_image': photo_image,
                'path': file_path,
                'size': image.size,
                'original_size': original_size,
                'rotation': 0,
                'current_image': image.copy()
            }

    def image_manipulation(self, image_id: int, action: str) -> None:
        """
        Выполняет манипуляции (изменение размера, поворот, зеркалирование) над изображением.
        """
        if image_id not in self.uploaded_images:
            return

        image_info = self.uploaded_images[image_id]
        current_image = image_info.get('current_image') or Image.open(image_info['path'])

        if action == "resize":
            size_input = askstring(
                "Изменение размера",
                f"Введите новый размер в формате 'ширина,высота' (текущий: {current_image.width}x{current_image.height}):"
            )
            if size_input:
                try:
                    width_str, height_str = size_input.split(",")
                    new_width, new_height = int(width_str.strip()), int(height_str.strip())
                    if 10 <= new_width <= 3000 and 10 <= new_height <= 3000:
                        current_image = current_image.resize((new_width, new_height), Image.LANCZOS)
                        image_info['size'] = (new_width, new_height)
                    else:
                        messagebox.showerror("Неверный размер", "Ширина и высота должны быть от 10 до 3000.")
                        return
                except (ValueError, AttributeError):
                    messagebox.showerror("Неверный ввод", "Введите два целых числа, разделённых запятой.")
                    return

        elif action == "rotate":
            image_info['rotation'] = (image_info['rotation'] + 90) % 360
            current_image = current_image.rotate(-90, expand=True)

        elif action == "mirror":
            current_image = current_image.transpose(Image.FLIP_LEFT_RIGHT)

        image_info['current_image'] = current_image
        photo_image = ImageTk.PhotoImage(current_image)
        self.canvas.canvas.itemconfig(image_id, image=photo_image)
        image_info['photo_image'] = photo_image

    def export_to_graphic_file(self, export_format: str) -> None:
        """
        Преобразует холст в изображение PIL
        и экспортирует его в графический файл.
        """
        file_ext = ".jpeg"
        file_path = filedialog.asksaveasfilename(defaultextension=file_ext,
                                                 filetypes=[(f"{export_format} files", f"*{file_ext}")])
        if not file_path:
            return

        items_data, images_data = self.objects_data_collector()
        canvas_width, canvas_height = self.canvas.canvas.winfo_width(), self.canvas.canvas.winfo_height()
        canvas_bg = self.canvas.canvas['background']

        pil_image = Image.new('RGB', (canvas_width, canvas_height), canvas_bg)
        draw = ImageDraw.Draw(pil_image)

        for item_data in items_data:
            self.draw_item_on_image(draw, item_data)

        for image_data in images_data:
            self.paste_image_on_image(pil_image, image_data)

        pil_image.save(file_path, format=export_format.upper())

    def draw_item_on_image(self, draw, item_data: Dict[str, Any]) -> None:
        """
        Отрисовывает объект на изображении PIL.
        """
        item_type = item_data['type']
        coords = item_data['coords']
        config = item_data.get('config', {})

        if item_type == 'text':
            font, font_size = self.get_font_to_pil(config.get('font', 'Arial 12'))
            draw.text(coords, config['text'], fill=config.get('fill'), font=font)

        else:
            draw_method = getattr(self, f"draw_{item_type}", None)
            if draw_method:
                draw_method(draw, coords, config)

    """
    Методы рисования фигур на изображении PIL.
    """

    def draw_line(self, draw, coords: Tuple[int, int], config: Dict[str, Any]) -> None:
        draw.line(coords, fill=config.get('fill'))

    def draw_rectangle(self, draw, coords: Tuple[int, int], config: Dict[str, Any]) -> None:
        draw.rectangle(coords, outline=config.get('outline'), fill=config.get('fill'))

    def draw_oval(self, draw, coords: Tuple[int, int], config: Dict[str, Any]) -> None:
        draw.ellipse(coords, outline=config.get('outline'), fill=config.get('fill'))

    def draw_triangle(self, draw, coords: Tuple[int, int], config: Dict[str, Any]) -> None:
        draw.polygon(coords, outline=config.get('outline'), fill=config.get('fill'))

    def paste_image_on_image(self, image, image_data: Dict[str, Any]) -> None:
        """
        Копирует изображение с холста на объект PIL.Image.
        """
        image_attr = self.uploaded_images[image_data['image_id']]
        image_path = image_data['path']
        coords = image_data['coords']
        image_size = image_attr['size']
        rotation = image_attr['rotation']

        try:
            with Image.open(image_path) as img:

                img.thumbnail(image_size)
                if rotation != 0:
                    img = img.rotate(rotation, expand=True)

                img.mode == "RGBA"
                paste_coords = (int(coords[0]), int(coords[1]))
                image.paste(img, paste_coords)

        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение. Ошибка: {error}")

    def get_font_to_pil(self, font_str: str) -> Tuple:
        """
        Преобразует строку шрифта из Tkinter в объект PIL ImageFont, включая обработку жирного начертания.
        """
        font_parts = font_str.split()
        def_font_name = "arial"
        font_style = ""

        for part in font_parts:
            if part.isdigit():
                font_size = int(part)

            elif part.lower() in ['bold']:
                font_style += part.lower().capitalize()

            else:
                font_name = part
        font_file_name = f"{font_name}{font_style}.ttf"

        try:
            font = ImageFont.truetype(font_file_name, font_size)
        except IOError:
            font = ImageFont.truetype(f"{def_font_name}.ttf", font_size)

        return font, font_size

    def reset_canvas_dialog(self) -> None:
        """
        Открывает диалог сохранения перед очисткой холста.
        """
        response = messagebox.askokcancel("Подтверждение", "Сохранить текущий холст перед очисткой?")
        if response:
            self.save_to_file()
        self.canvas.reset_canvas()