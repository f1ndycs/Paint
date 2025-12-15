from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List, Dict, Any
import json
from canvas import DrawingCanvas


class FileManager:
    """
    Класс менеджера файлов, отвечает за сохранение и загрузку холста и изображений.
    """

    def __init__(self, canvas: DrawingCanvas) -> None:
        """
        Конструктор менеджера файлов.
        """
        self.canvas = canvas


    def objects_data_collector(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Собирает данные обо всех объектах, размещённых на холсте,
        для последующего восстановления.
        """
        items_data = []

        for item in self.canvas.canvas.find_all():
            item_tags = self.canvas.canvas.gettags(item)
            item_type = self.canvas.canvas.type(item)
            item_config = self.get_item_config(item, item_type)

            items_data.append({
                'type': item_type,
                'coords': self.canvas.canvas.coords(item),
                'tags': item_tags,
                'config': item_config})

        return items_data

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
        items_data = self.objects_data_collector()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:

            try:
                with open(file_path, 'w') as file:
                    json.dump({'drawings': items_data, 'background': self.canvas.bg}, file, indent=4)
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

                    if 'background' in items_data:
                        self.canvas.update_background(items_data['background'])

                    for item_data in items_data.get('drawings', []):
                        self.create_item(item_data)

                    # Отправляем изменения на сервер
                    self._update_canvas_state()

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

        if item_type in ['line', 'rectangle', 'oval', 'text', 'polygon']:
            getattr(self.canvas.canvas, 'create_' + item_type)(coords, **config, tags=tags)

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

        items_data = self.objects_data_collector()
        canvas_width, canvas_height = self.canvas.canvas.winfo_width(), self.canvas.canvas.winfo_height()
        canvas_bg = self.canvas.canvas['background']

        pil_image = Image.new('RGB', (canvas_width, canvas_height), canvas_bg)
        draw = ImageDraw.Draw(pil_image)

        for item_data in items_data:
            self.draw_item_on_image(draw, item_data)

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

    def draw_polygon(self, draw, coords: Tuple[int, int], config: Dict[str, Any]) -> None:
        draw.polygon(coords, outline=config.get('outline'), fill=config.get('fill'))

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

    def load_canvas_state(self, state: Dict[str, Any]) -> None:
        """
        Загружает состояние холста из переданных данных
        """
        self.canvas.reset_canvas()
        self.canvas.update_background(state['background'])

        for item_data in state['drawings']:
            self.create_item(item_data)

    def _update_canvas_state(self):
        """Вспомогательный метод для отправки состояния холста"""
        if hasattr(self.canvas.root, 'network') and self.canvas.root.network.connected:
            items_data = self.objects_data_collector()
            self.canvas.root.network.send({
                'type': 'draw',
                'data': {
                    'drawings': items_data,
                    'background': self.canvas.bg
                }
            })