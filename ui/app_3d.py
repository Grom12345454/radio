import tkinter as tk
from tkinter import ttk
import math

# Импорты из корневой папки проекта
from config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    DEFAULT_VOLUME, UI_UPDATE_INTERVAL, ACCENT, ACCENT_HOVER, BG, PANEL,
    PANEL_LIGHT, PANEL_HOVER, TEXT, TEXT_MUTED, SUCCESS, WARNING, ERROR,
)
from stations import STATIONS, search_stations
from player import RadioPlayer


class RadioApp3D:
    def __init__(self, root):
        self.root = root
        
        # Параметры 3D эффекта
        self.tilt_x = 0.0
        self.tilt_y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.sensitivity = 25  # Чувствительность к мыши
        
        # --------------------------------------------------------
        # WINDOW SETUP
        # --------------------------------------------------------
        self.root.title(f"{APP_NAME} {APP_VERSION} [3D]")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg="#000000")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --------------------------------------------------------
        # STATE
        # --------------------------------------------------------
        self.current_station = None
        self.current_url = None
        self.filtered_stations = list(STATIONS.keys())
        self.closing = False
        self.updating_volume = False
        self.station_tiles = {}

        # --------------------------------------------------------
        # PLAYER
        # --------------------------------------------------------
        self.player = RadioPlayer()
        self.player.set_callbacks(
            on_state_changed=self.player_state_changed,
            on_error=self.player_error,
        )

        # --------------------------------------------------------
        # 3D SCENE CANVAS
        # --------------------------------------------------------
        # Используем Canvas как "сцену" для перемещения интерфейса
        self.scene = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.scene.pack(fill="both", expand=True)
        
        # Контейнер всего UI
        self.ui_frame = tk.Frame(self.scene, bg=BG)
        
        # Создаем окно на канвасе. ВАЖНО: начальные координаты точно в центре
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        
        self.window_id = self.scene.create_window(
            self.center_x, 
            self.center_y, 
            window=self.ui_frame, 
            anchor="center"
        )

        # Отслеживание мыши для параллакса
        self.root.bind("<Motion>", self._on_mouse_move)
        
        # --------------------------------------------------------
        # BUILD INTERFACE
        # --------------------------------------------------------
        self.setup_styles()
        self.build_ui()
        self.setup_hotkeys()

        # Init volume & stations
        self.updating_volume = True
        try: self.volume_scale.set(DEFAULT_VOLUME)
        finally: self.updating_volume = False
        
        self.player.set_volume(DEFAULT_VOLUME)
        self.update_volume_icon(DEFAULT_VOLUME)
        self.populate_stations()
        
        # Запуск циклов
        self.animate_loop()
        self.update_loop()

    # ============================================================
    # 3D ANIMATION LOGIC (FIXED)
    # ============================================================
    def _on_mouse_move(self, event):
        # Нормализуем координаты мыши от -1 до 1 относительно центра
        cx = self.root.winfo_width() / 2
        cy = self.root.winfo_height() / 2
        
        # Если окно еще не отрисовано, пропускаем
        if cx == 0 or cy == 0: return
            
        mx = (event.x - cx) / cx
        my = (event.y - cy) / cy
        
        # Целевая позиция смещения
        self.target_x = mx * self.sensitivity
        self.target_y = my * self.sensitivity

    def animate_loop(self):
        if self.closing: return
        
        # Плавная интерполяция (Lerp) для мягкости движения
        self.tilt_x += (self.target_x - self.tilt_x) * 0.08
        self.tilt_y += (self.target_y - self.tilt_y) * 0.08
        
        # Безопасное перемещение окна на канвасе
        # Мы просто двигаем центр окна от исходной точки
        new_x = self.center_x + self.tilt_x
        new_y = self.center_y + self.tilt_y
        
        # Ограничиваем, чтобы не улетело слишком далеко (опционально)
        # Но для эффекта "улетания" можно оставить свободным
        
        self.scene.coords(self.window_id, new_x, new_y)
        
        # Легкий поворот через scale (только по осям, без изменения размера контента)
        # Это создает эффект перспективы без ломания верстки
        # scale_x = 1.0 + (self.tilt_y * 0.002)
        # scale_y = 1.0 + (self.tilt_x * 0.002)
        # self.scene.scale(self.window_id, new_x, new_y, scale_x, scale_y)
        
        self.root.after(16, self.animate_loop) # ~60 FPS

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Modern.TButton", background=ACCENT, foreground="white", borderwidth=0, padding=(20, 12), font=("Segoe UI", 11, "bold"))
        style.map("Modern.TButton", background=[("active", ACCENT_HOVER)])
        style.configure("Secondary.TButton", background=PANEL_LIGHT, foreground=TEXT, borderwidth=0, padding=(15, 12), font=("Segoe UI", 10))

    def build_ui(self):
        # HEADER
        header = tk.Frame(self.ui_frame, bg=BG)
        header.pack(fill="x", padx=40, pady=(30, 20))
        
        tk.Label(header, text="📻", bg=BG, fg=ACCENT, font=("Segoe UI Emoji", 40)).pack(side="left", padx=(0, 15))
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text=APP_NAME, bg=BG, fg="white", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Immersive 3D Experience", bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w")

        # MAIN LAYOUT
        main = tk.Frame(self.ui_frame, bg=BG)
        main.pack(fill="both", expand=True, padx=40, pady=10)

        # LEFT PANEL
        left = tk.Frame(main, bg=PANEL, width=400)
        left.pack(side="left", fill="y", padx=(0, 20))
        left.pack_propagate(False)
        
        tk.Label(left, text="КАТЕГОРИИ", bg=PANEL, fg=ACCENT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=25, pady=(25, 15))

        # SEARCH
        search_box = tk.Frame(left, bg="#1a1b26")
        search_box.pack(fill="x", padx=20, pady=(0, 20))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_box, textvariable=self.search_var, bg="#1a1b26", fg=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 11))
        self.search_entry.pack(fill="x", padx=15, pady=12)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # GRID CONTAINER
        list_frame = tk.Frame(left, bg=PANEL)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
        scrollbar = tk.Scrollbar(list_frame, bg=PANEL, troughcolor=PANEL, activebackground=ACCENT, relief="flat", borderwidth=0, width=10)
        scrollbar.pack(side="right", fill="y")
        
        self.station_canvas = tk.Canvas(list_frame, bg=PANEL, highlightthickness=0, yscrollcommand=scrollbar.set)
        self.station_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.station_canvas.yview)
        
        self.station_grid_container = tk.Frame(self.station_canvas, bg=PANEL)
        self.station_canvas.create_window((0, 0), window=self.station_grid_container, anchor="nw")
        self.station_grid_container.bind("<Configure>", lambda e: self.station_canvas.configure(scrollregion=self.station_canvas.bbox("all")))
        self.station_canvas.bind_all("<MouseWheel>", lambda e: self.station_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # RIGHT PANEL
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # INFO CARD
        station_card = tk.Frame(right, bg=PANEL, height=200)
        station_card.pack(fill="x", pady=(0, 20))
        station_card.pack_propagate(False)
        
        self.cover = tk.Canvas(station_card, width=150, height=150, bg="#1a1b26", highlightthickness=0)
        self.cover.pack(side="left", padx=30, pady=25)
        self.cover.create_text(75, 75, text="♪", fill=ACCENT, font=("Segoe UI", 60, "bold"))
        
        info = tk.Frame(station_card, bg=PANEL)
        info.pack(side="left", fill="both", expand=True, padx=(0, 30))
        
        self.station_title = tk.Label(info, text="Выберите станцию", bg=PANEL, fg="white", font=("Segoe UI", 24, "bold"), wraplength=500, justify="left")
        self.station_title.pack(anchor="w", pady=(35, 8))
        
        self.status = tk.Label(info, text="● Готов к работе", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 11))
        self.status.pack(anchor="w")
        
        self.track = tk.Label(info, text="", bg=PANEL, fg=ACCENT, font=("Segoe UI", 10, "italic"))
        self.track.pack(anchor="w", pady=(15, 0))

        # CONTROLS BAR
        controls = tk.Frame(right, bg=PANEL_LIGHT)
        controls.pack(fill="x")
        
        btn_box = tk.Frame(controls, bg=PANEL_LIGHT)
        btn_box.pack(side="left", padx=20, pady=15)
        
        self.play_button = ttk.Button(btn_box, text="▶ PLAY", style="Modern.TButton", command=self.toggle_play)
        self.play_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(btn_box, text="■ STOP", style="Secondary.TButton", command=self.stop)
        self.stop_button.pack(side="left", padx=5)
        
        vol_box = tk.Frame(controls, bg=PANEL_LIGHT)
        vol_box.pack(side="right", padx=25)
        
        self.volume_icon = tk.Label(vol_box, text="", bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI Emoji", 14))
        self.volume_icon.pack(side="left", padx=(0, 10))
        
        self.volume_scale = tk.Scale(vol_box, from_=0, to=100, orient="horizontal", length=150, showvalue=False, bg=PANEL_LIGHT, fg=TEXT, troughcolor="#2a2b3d", activebackground=ACCENT, highlightthickness=0, borderwidth=0, relief="flat", sliderrelief="flat", sliderlength=20, width=12, command=self.volume_changed)
        self.volume_scale.pack(side="left")

        # FOOTER
        footer = tk.Frame(self.ui_frame, bg="#0a0a0f", height=35)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        self.footer_status = tk.Label(footer, text="● OFFLINE", bg="#0a0a0f", fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.footer_status.pack(side="left", padx=20, pady=8)
        tk.Label(footer, text=f"{APP_NAME} {APP_VERSION}", bg="#0a0a0f", fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="right", padx=20)

    def setup_hotkeys(self):
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Escape>", lambda e: self.stop())

    # ============================================================
    # STATION LOGIC
    # ============================================================
    def populate_stations(self):
        for w in self.station_grid_container.winfo_children(): w.destroy()
        self.station_tiles.clear()
        
        col, row, cols = 0, 0, 2
        for name in self.filtered_stations:
            tile = self._create_3d_tile(name)
            tile.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.station_grid_container.columnconfigure(col, weight=1)
            col += 1
            if col >= cols: col, row = 0, row + 1

    def _create_3d_tile(self, name):
        frame = tk.Frame(self.station_grid_container, bg=PANEL_LIGHT, cursor="hand2", bd=0)
        
        # 3D Shadow effect
        shadow = tk.Frame(frame, bg="#000000", height=4)
        shadow.pack(side="bottom", fill="x")
        
        content = tk.Frame(frame, bg=PANEL_LIGHT)
        content.pack(fill="both", expand=True, padx=12, pady=12)
        
        icon = tk.Label(content, text="📻", bg=PANEL_LIGHT, fg=ACCENT, font=("Segoe UI Emoji", 18))
        icon.pack(side="left", padx=(0, 10))
        
        label = tk.Label(content, text=name, bg=PANEL_LIGHT, fg="white", font=("Segoe UI", 9, "bold"), anchor="w", wraplength=140)
        label.pack(side="left", fill="x", expand=True)
        
        def enter(e):
            frame.configure(bg=ACCENT); content.configure(bg=ACCENT)
            icon.configure(bg=ACCENT, fg="white"); label.configure(bg=ACCENT, fg="white")
            
        def leave(e):
            if self.current_station != name:
                frame.configure(bg=PANEL_LIGHT); content.configure(bg=PANEL_LIGHT)
                icon.configure(bg=PANEL_LIGHT, fg=ACCENT); label.configure(bg=PANEL_LIGHT, fg="white")
                
        frame.bind("<Enter>", enter)
        frame.bind("<Leave>", leave)
        frame.bind("<Button-1>", lambda e, n=name: self._select_station(n))
        
        self.station_tiles[name] = {"frame": frame, "content": content, "icon": icon, "label": label}
        return frame

    def _select_station(self, name):
        self.current_station = name
        url = STATIONS.get(name)
        if not url: return self.player_error("URL не найден")
            
        self.current_url = url
        self.station_title.config(text=name)
        self.track.config(text="")
        self.set_status("● Подключение...", WARNING)
        self.footer_status.config(text="● CONNECTING", fg=WARNING)
        self.play_button.config(text="⏸ PAUSE")
        
        for s_name, w in self.station_tiles.items():
            is_active = (s_name == name)
            bg = ACCENT if is_active else PANEL_LIGHT
            fg = "white" if is_active else ACCENT
            
            w["frame"].configure(bg=bg); w["content"].configure(bg=bg)
            w["icon"].configure(bg=bg, fg=fg); w["label"].configure(bg=bg, fg="white")

        try: self.player.play(name, url)
        except Exception as exc: self.player_error(str(exc))

    def on_search(self, e=None):
        self.filtered_stations = search_stations(self.search_var.get())
        self.populate_stations()

    def toggle_play(self):
        if not self.current_station:
            if self.filtered_stations: self._select_station(self.filtered_stations[0])
            return
        state = self.player.get_state()
        if state == "PLAYING": self.player.pause()
        elif state == "PAUSED": self.player.resume()
        elif state in ("STOPPED", "ERROR", "ENDED"):
            if self.current_url: self.player.play(self.current_station, self.current_url)

    def stop(self):
        try: self.player.stop()
        except: pass
        self.play_button.config(text="▶ PLAY")
        self.set_status("● Остановлено", TEXT_MUTED)
        self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)

    def player_state_changed(self, state):
        if self.closing: return
        map = {
            "PLAYING": ("● Сейчас играет", SUCCESS, "● LIVE", SUCCESS, "⏸ PAUSE"),
            "PAUSED": ("● Пауза", TEXT_MUTED, "● PAUSED", TEXT_MUTED, "▶ RESUME"),
            "ERROR": ("● Ошибка", ERROR, "● ERROR", ERROR, "▶ PLAY"),
            "STOPPED": ("● Остановлено", TEXT_MUTED, "● OFFLINE", TEXT_MUTED, "▶ PLAY"),
        }
        if state in map:
            t, c, ft, fc, bt = map[state]
            self.set_status(t, c)
            self.footer_status.config(text=ft, fg=fc)
            self.play_button.config(text=bt)

    def player_error(self, text):
        self.set_status("● Ошибка", ERROR)
        self.footer_status.config(text="● ERROR", fg=ERROR)

    def set_status(self, text, color):
        try: self.status.config(text=text, fg=color)
        except: pass

    def volume_changed(self, val):
        if self.updating_volume: return
        val = max(0, min(100, int(float(val))))
        self.player.set_volume(val)
        self.update_volume_icon(val)

    def update_volume_icon(self, val):
        icons = {0: "🔇", 40: "", 75: ""}
        icon = ""
        for th, i in sorted(icons.items()):
            if val >= th and i: icon = i
        try: self.volume_icon.config(text=icon)
        except: pass

    def update_loop(self):
        if self.closing: return
        try:
            if self.player.get_state() == "PLAYING":
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
            title = self.player.get_title()
            if title: self.track.config(text=f"♪ {title}")
        except: pass
        try: self.root.after(UI_UPDATE_INTERVAL, self.update_loop)
        except: pass

    def on_closing(self):
        self.closing = True
        try: self.player.destroy()
        except: pass
        try: self.root.destroy()
        except: pass