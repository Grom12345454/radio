import math
import random


class Visualizer3D:
    def __init__(self, canvas, color="#3b82f6", secondary_color="#8b5cf6"):
        self.canvas = canvas
        self.color = color
        self.secondary_color = secondary_color
        
        self.enabled = True
        self.bars = []
        self.num_bars = 32
        self.phase = 0
        
        # Параметры 3D эффекта
        self.depth_factor = 0.6
        self.perspective_factor = 0.8
        
    def draw(self, active=False):
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Очистка фона с градиентом
        self._draw_background(width, height)
        
        if active:
            self._draw_3d_visualizer(width, height)
        else:
            self._draw_idle_animation(width, height)
        
        self.phase += 0.05
    
    def _draw_background(self, width, height):
        """Рисует градиентный фон"""
        # Создаем эффект глубины
        for i in range(5):
            alpha = 0.1 - (i * 0.02)
            y_offset = i * 20
            
            self.canvas.create_rectangle(
                0, y_offset, width, height,
                fill=f"#111827",
                outline=""
            )
    
    def _draw_3d_visualizer(self, width, height):
        """Рисует 3D визуализатор с эффектом перспективы"""
        bar_width = max(8, width // (self.num_bars * 2))
        gap = bar_width // 2
        
        center_x = width // 2
        center_y = height // 2
        
        # Рисуем полосы с 3D эффектом
        for i in range(self.num_bars):
            # Генерируем высоту с волновым эффектом
            wave = math.sin(self.phase + i * 0.3) * 0.5 + 0.5
            noise = random.uniform(0.7, 1.0)
            
            base_height = int(height * 0.6)
            level = int(base_height * wave * noise)
            
            # Позиция с перспективой
            offset_from_center = i - self.num_bars // 2
            perspective_scale = 1 - abs(offset_from_center) * 0.02
            
            x_pos = center_x + offset_from_center * (bar_width + gap) * perspective_scale
            bar_w = int(bar_width * perspective_scale)
            
            # 3D эффект - рисуем несколько слоев
            layers = 3
            for layer in range(layers):
                depth_offset = layer * 3
                layer_alpha = 1 - (layer * 0.3)
                
                # Цвет с градиентом
                if layer == 0:
                    fill_color = self.color
                elif layer == 1:
                    fill_color = self.secondary_color
                else:
                    fill_color = "#6366f1"
                
                y_pos = height - level + depth_offset
                
                # Основная полоса
                self.canvas.create_rectangle(
                    x_pos - bar_w // 2,
                    y_pos,
                    x_pos + bar_w // 2,
                    height + depth_offset,
                    fill=fill_color,
                    outline="",
                    stipple="" if layer == 0 else "gray50"
                )
                
                # Блик сверху
                if layer == 0:
                    self.canvas.create_rectangle(
                        x_pos - bar_w // 2,
                        y_pos,
                        x_pos + bar_w // 2,
                        y_pos + 3,
                        fill="white",
                        outline="",
                        stipple="gray25"
                    )
    
    def _draw_idle_animation(self, width, height):
        """Рисует анимацию в режиме ожидания"""
        center_x = width // 2
        center_y = height // 2
        
        # Пульсирующий круг
        pulse = math.sin(self.phase * 2) * 0.3 + 0.7
        radius = int(min(width, height) * 0.15 * pulse)
        
        # Внешнее свечение
        for i in range(3, 0, -1):
            glow_radius = radius + i * 10
            alpha = 0.1 / i
            
            self.canvas.create_oval(
                center_x - glow_radius,
                center_y - glow_radius,
                center_x + glow_radius,
                center_y + glow_radius,
                fill=self.color,
                outline="",
                stipple="gray75"
            )
        
        # Основной круг
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=self.color,
            outline=self.secondary_color,
            width=2
        )
        
        # Внутренний символ
        self.canvas.create_text(
            center_x,
            center_y,
            text="♪",
            fill="white",
            font=("Segoe UI", int(radius * 0.8), "bold")
        )
        
        # Волны вокруг
        for i in range(3):
            wave_radius = radius + 30 + i * 20
            wave_offset = math.sin(self.phase + i) * 5
            
            self.canvas.create_oval(
                center_x - wave_radius + wave_offset,
                center_y - wave_radius,
                center_x + wave_radius + wave_offset,
                center_y + wave_radius,
                fill="",
                outline=self.secondary_color,
                width=1,
                stipple="gray50"
            )