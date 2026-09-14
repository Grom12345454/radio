import random
import math

class Visualizer:
    def __init__(self, canvas, color="#6C63FF"):
        self.canvas = canvas
        self.color = color
        self.enabled = True
        
        # Для плавности можно хранить предыдущие значения
        self.prev_levels = []

    def draw(self, active=False):
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        bar_width = 8
        gap = 4
        count = max(1, int(width / (bar_width + gap)))

        # Инициализируем массив уровней, если он пуст или изменилось количество столбцов
        if len(self.prev_levels) != count:
            self.prev_levels = [0] * count

        for i in range(count):
            if active:
                # Генерируем уровень с учетом "волны" для красоты
                target_level = random.randint(int(height * 0.1), int(height * 0.9))
                
                # Плавное изменение от предыдущего значения
                current = self.prev_levels[i]
                diff = target_level - current
                level = int(current + diff * 0.3) # Коэффициент плавности
                
                # Ограничиваем минимумом
                level = max(10, level)
                
                self.prev_levels[i] = level
            else:
                level = 3
                self.prev_levels[i] = level

            x1 = i * (bar_width + gap)
            x2 = x1 + bar_width
            y1 = height - level
            y2 = height

            # Рисуем скругленные столбцы (в Tkinter это делается через овалы или просто прямоугольники)
            # Для простоты и производительности используем прямоугольники, но с цветом
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=self.color,
                outline=""
            )
            
            # Добавляем "шапку" столбца другого цвета для стиля
            if active and level > 10:
                cap_height = 4
                self.canvas.create_rectangle(
                    x1, y1, x2, y1 + cap_height,
                    fill="#FFFFFF",
                    outline=""
                )