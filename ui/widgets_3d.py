import tkinter as tk


class StationCard3D(tk.Frame):
    """Современная 3D карточка радиостанции с эффектом стекла"""
    
    def __init__(self, parent, station_name, station_url="", genre="", 
                 on_click_callback=None, is_playing=False, now_playing="", **kwargs):
        super().__init__(parent, bg="#111827", **kwargs)
        
        self.station_name = station_name
        self.station_url = station_url
        self.genre = genre
        self.is_selected = False
        self.is_playing = is_playing
        self.now_playing = now_playing
        self.on_click_callback = on_click_callback
        
        # Основной контейнер с закругленными углами (имитация)
        self.card_frame = tk.Frame(self, bg="#1f2937", relief="flat")
        self.card_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Верхняя часть: иконка + название + жанр
        top_frame = tk.Frame(self.card_frame, bg="#1f2937")
        top_frame.pack(fill="x", padx=12, pady=(12, 6))
        
        # Иконка радио
        icon_size = 40
        self.icon_canvas = tk.Canvas(
            top_frame,
            width=icon_size,
            height=icon_size,
            bg="#1f2937",
            highlightthickness=0,
            borderwidth=0
        )
        self.icon_canvas.pack(side="left", padx=(0, 12))
        
        # Рисуем иконку
        self._draw_icon()
        
        # Название и жанр
        info_frame = tk.Frame(top_frame, bg="#1f2937")
        info_frame.pack(side="left", fill="both", expand=True)
        
        self.name_label = tk.Label(
            info_frame,
            text=station_name,
            bg="#1f2937",
            fg="#f9fafb",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        self.name_label.pack(anchor="w")
        
        if genre:
            self.genre_label = tk.Label(
                info_frame,
                text=genre,
                bg="#1f2937",
                fg="#6b7280",
                font=("Segoe UI", 8),
                anchor="w"
            )
            self.genre_label.pack(anchor="w", pady=(2, 0))
        
        # Индикатор воспроизведения
        self.play_indicator = tk.Canvas(
            top_frame,
            width=24,
            height=24,
            bg="#1f2937",
            highlightthickness=0
        )
        self.play_indicator.pack(side="right")
        
        # Нижняя часть: что играет
        if now_playing:
            bottom_frame = tk.Frame(self.card_frame, bg="#1f2937")
            bottom_frame.pack(fill="x", padx=12, pady=(0, 10))
            
            tk.Label(
                bottom_frame,
                text="♪ Сейчас играет:",
                bg="#1f2937",
                fg="#9ca3af",
                font=("Segoe UI", 8),
                anchor="w"
            ).pack(anchor="w")
            
            self.now_playing_label = tk.Label(
                bottom_frame,
                text=now_playing,
                bg="#1f2937",
                fg="#3b82f6",
                font=("Segoe UI", 9),
                anchor="w",
                wraplength=250
            )
            self.now_playing_label.pack(anchor="w", pady=(2, 0))
        
        # Bind events
        self.bind("<Button-1>", self.handle_click)
        self.card_frame.bind("<Button-1>", self.handle_click)
        self.icon_canvas.bind("<Button-1>", self.handle_click)
        self.name_label.bind("<Button-1>", self.handle_click)
        self.play_indicator.bind("<Button-1>", self.handle_click)
        
        if hasattr(self, 'genre_label'):
            self.genre_label.bind("<Button-1>", self.handle_click)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.card_frame.bind("<Enter>", self.on_enter)
        self.card_frame.bind("<Leave>", self.on_leave)
    
    def _draw_icon(self):
        """Рисует иконку радиостанции"""
        canvas = self.icon_canvas
        
        # Фон иконки
        canvas.create_oval(
            2, 2, 38, 38,
            fill="#3b82f6",
            outline=""
        )
        
        # Символ радио
        canvas.create_text(
            20, 20,
            text="📻",
            fill="white",
            font=("Segoe UI Emoji", 18)
        )
    
    def handle_click(self, event=None):
        """Обработчик клика"""
        if self.on_click_callback:
            self.on_click_callback(self)
    
    def on_enter(self, event=None):
        if not self.is_selected:
            self.card_frame.config(bg="#374151")
            for child in self.card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg="#374151")
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label):
                            grandchild.config(bg="#374151")
                        elif isinstance(grandchild, tk.Canvas):
                            grandchild.config(bg="#374151")
                elif isinstance(child, tk.Label):
                    child.config(bg="#374151")
                elif isinstance(child, tk.Canvas):
                    child.config(bg="#374151")
    
    def on_leave(self, event=None):
        if not self.is_selected:
            self.card_frame.config(bg="#1f2937")
            for child in self.card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg="#1f2937")
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label):
                            grandchild.config(bg="#1f2937")
                        elif isinstance(grandchild, tk.Canvas):
                            grandchild.config(bg="#1f2937")
                elif isinstance(child, tk.Label):
                    child.config(bg="#1f2937")
                elif isinstance(child, tk.Canvas):
                    child.config(bg="#1f2937")
    
    def select(self):
        """Выделить карточку"""
        self.is_selected = True
        self.card_frame.config(bg="#1e3a8a", highlightbackground="#3b82f6", highlightthickness=2)
        
        # Обновляем цвета всех дочерних элементов
        self._update_colors("#1e3a8a", "#60a5fa")
    
    def deselect(self):
        """Снять выделение"""
        self.is_selected = False
        self.card_frame.config(bg="#1f2937", highlightthickness=0)
        self._update_colors("#1f2937", "#f9fafb")
    
    def _update_colors(self, bg_color, text_color):
        """Обновляет цвета всех элементов карточки"""
        for child in self.card_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=bg_color)
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, tk.Label):
                        current_text = grandchild.cget("text")
                        if "Сейчас играет" not in current_text:
                            grandchild.config(bg=bg_color, fg=text_color)
                        else:
                            grandchild.config(bg=bg_color)
                    elif isinstance(grandchild, tk.Canvas):
                        grandchild.config(bg=bg_color)
            elif isinstance(child, tk.Label):
                current_text = child.cget("text")
                if "Сейчас играет" not in current_text:
                    child.config(bg=bg_color, fg=text_color)
                else:
                    child.config(bg=bg_color)
            elif isinstance(child, tk.Canvas):
                child.config(bg=bg_color)
    
    def update_now_playing(self, track_info):
        """Обновить информацию о текущем треке"""
        if hasattr(self, 'now_playing_label'):
            self.now_playing_label.config(text=track_info)


class Button3D(tk.Button):
    """3D кнопка с эффектом нажатия"""
    
    def __init__(self, parent, text="", command=None, bg="#3b82f6", fg="white", **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            **kwargs
        )
        
        self.default_bg = bg
        self.pressed_bg = self._darken_color(bg, 20)
        
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def _darken_color(self, hex_color, percent):
        rgb = self._hex_to_rgb(hex_color)
        rgb = tuple(max(0, int(c * (1 - percent/100))) for c in rgb)
        return self._rgb_to_hex(rgb)
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def on_press(self, event=None):
        self.config(bg=self.pressed_bg)
    
    def on_release(self, event=None):
        self.config(bg=self.default_bg)
    
    def on_enter(self, event=None):
        self.config(bg=self._lighten_color(self.default_bg, 10))
    
    def on_leave(self, event=None):
        self.config(bg=self.default_bg)
    
    def _lighten_color(self, hex_color, percent):
        rgb = self._hex_to_rgb(hex_color)
        rgb = tuple(min(255, int(c * (1 + percent/100))) for c in rgb)
        return self._rgb_to_hex(rgb)


class VolumeSlider3D(tk.Scale):
    """3D слайдер громкости"""
    
    def __init__(self, parent, command=None, **kwargs):
        default_kwargs = {
            'from_': 0,
            'to': 100,
            'orient': 'horizontal',
            'showvalue': False,
            'bg': '#1f2937',
            'fg': '#f9fafb',
            'troughcolor': '#374151',
            'activebackground': '#3b82f6',
            'highlightthickness': 0,
            'borderwidth': 0,
            'relief': 'flat',
            'sliderrelief': 'flat',
            'sliderlength': 20,
            'width': 12,
            'command': command
        }
        
        default_kwargs.update(kwargs)
        super().__init__(parent, **default_kwargs)