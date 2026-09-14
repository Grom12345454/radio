import tkinter as tk
from tkinter import ttk

# Импорты из корневой папки проекта
from config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    DEFAULT_VOLUME, UI_UPDATE_INTERVAL, ACCENT, ACCENT_HOVER, BG, PANEL,
    PANEL_LIGHT, PANEL_HOVER, TEXT, TEXT_MUTED, SUCCESS, WARNING, ERROR,
)
from stations import STATIONS, search_stations
from player import RadioPlayer


class RadioApp3D:  # Имя класса оставлено для совместимости с main.py
    def __init__(self, root):
        self.root = root
        
        # --------------------------------------------------------
        # WINDOW SETUP (Стандартное 2D окно)
        # --------------------------------------------------------
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=BG)
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
        # UI BUILD
        # --------------------------------------------------------
        self.setup_styles()
        self.build_ui()
        self.setup_hotkeys()

        # Init
        self.updating_volume = True
        try: self.volume_scale.set(DEFAULT_VOLUME)
        finally: self.updating_volume = False
        
        self.player.set_volume(DEFAULT_VOLUME)
        self.update_volume_icon(DEFAULT_VOLUME)
        
        # Заполняем станции сразу при запуске
        self.populate_stations()
        
        self.update_loop()

    # ============================================================
    # STYLES
    # ============================================================
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Кнопка Play
        style.configure("Modern.TButton", 
            background=ACCENT, foreground="white", borderwidth=0, 
            padding=(25, 12), font=("Segoe UI", 11, "bold")
        )
        style.map("Modern.TButton", background=[("active", ACCENT_HOVER)])
        
        # Кнопка Stop
        style.configure("Secondary.TButton", 
            background=PANEL_LIGHT, foreground=TEXT, borderwidth=0, 
            padding=(20, 12), font=("Segoe UI", 10)
        )
        style.map("Secondary.TButton", background=[("active", PANEL_HOVER)])

    # ============================================================
    # INTERFACE CONSTRUCTION
    # ============================================================
    def build_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=40, pady=(30, 20))
        
        tk.Label(header, text="", bg=BG, fg=ACCENT, font=("Segoe UI Emoji", 40)).pack(side="left", padx=(0, 15))
        
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text=APP_NAME, bg=BG, fg="white", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Internet Radio Player", bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w")

        # --- MAIN CONTENT ---
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=40, pady=10)

        # --- LEFT PANEL (STATIONS) ---
        left_panel = tk.Frame(main, bg=PANEL, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="КАТЕГОРИИ", bg=PANEL, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=25, pady=(20, 15)
        )

        # Search Bar
        search_frame = tk.Frame(left_panel, bg="#1a1b26")
        search_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, bg="#1a1b26", fg=TEXT,
            insertbackground=TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 11)
        )
        self.search_entry.pack(fill="x", padx=15, pady=12)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Scrollable Grid Area
        grid_container_outer = tk.Frame(left_panel, bg=PANEL)
        grid_container_outer.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
        # Custom Scrollbar styling
        scrollbar = tk.Scrollbar(grid_container_outer, bg=PANEL, troughcolor=PANEL, activebackground=ACCENT, relief="flat", borderwidth=0, width=10)
        scrollbar.pack(side="right", fill="y")
        
        self.station_canvas = tk.Canvas(grid_container_outer, bg=PANEL, highlightthickness=0, yscrollcommand=scrollbar.set)
        self.station_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.station_canvas.yview)
        
        self.station_grid = tk.Frame(self.station_canvas, bg=PANEL)
        self.station_canvas.create_window((0, 0), window=self.station_grid, anchor="nw")
        
        self.station_grid.bind("<Configure>", lambda e: self.station_canvas.configure(scrollregion=self.station_canvas.bbox("all")))
        # Fix mousewheel for canvas
        self.station_canvas.bind_all("<MouseWheel>", lambda e: self.station_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # --- RIGHT PANEL (PLAYER) ---
        right_panel = tk.Frame(main, bg=BG)
        right_panel.pack(side="left", fill="both", expand=True)

        # Info Card
        info_card = tk.Frame(right_panel, bg=PANEL, height=220)
        info_card.pack(fill="x", pady=(0, 20))
        info_card.pack_propagate(False)
        
        # Cover Art Placeholder
        self.cover_canvas = tk.Canvas(info_card, width=160, height=160, bg="#1a1b26", highlightthickness=0)
        self.cover_canvas.pack(side="left", padx=35, pady=30)
        self.cover_canvas.create_text(80, 80, text="♪", fill=ACCENT, font=("Segoe UI", 70, "bold"))
        
        # Text Info
        text_area = tk.Frame(info_card, bg=PANEL)
        text_area.pack(side="left", fill="both", expand=True, padx=(0, 40), pady=30)
        
        self.station_title_label = tk.Label(text_area, text="Выберите станцию", bg=PANEL, fg="white", font=("Segoe UI", 26, "bold"), wraplength=500, justify="left")
        self.station_title_label.pack(anchor="w", pady=(10, 5))
        
        self.status_label = tk.Label(text_area, text="● Готов к воспроизведению", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 11))
        self.status_label.pack(anchor="w")
        
        self.track_label = tk.Label(text_area, text="", bg=PANEL, fg=ACCENT, font=("Segoe UI", 10, "italic"))
        self.track_label.pack(anchor="w", pady=(15, 0))

        # Controls Bar
        controls_bar = tk.Frame(right_panel, bg=PANEL_LIGHT)
        controls_bar.pack(fill="x", side="bottom") # Прижимаем к низу правой панели
        
        btn_area = tk.Frame(controls_bar, bg=PANEL_LIGHT)
        btn_area.pack(side="left", padx=25, pady=20)
        
        self.play_btn = ttk.Button(btn_area, text="▶ PLAY", style="Modern.TButton", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(btn_area, text="■ STOP", style="Secondary.TButton", command=self.stop)
        self.stop_btn.pack(side="left", padx=5)
        
        vol_area = tk.Frame(controls_bar, bg=PANEL_LIGHT)
        vol_area.pack(side="right", padx=30, pady=20)
        
        self.vol_icon = tk.Label(vol_area, text="", bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI Emoji", 16))
        self.vol_icon.pack(side="left", padx=(0, 12))
        
        # Styled Scale
        self.volume_scale = tk.Scale(
            vol_area, from_=0, to=100, orient="horizontal", length=160, showvalue=False,
            bg=PANEL_LIGHT, fg=TEXT, troughcolor="#2a2b3d", activebackground=ACCENT,
            highlightthickness=0, borderwidth=0, relief="flat", sliderrelief="flat",
            sliderlength=22, width=14, command=self.volume_changed
        )
        self.volume_scale.pack(side="left")

        # --- FOOTER ---
        footer = tk.Frame(self.root, bg="#0a0a0f", height=35)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        self.footer_status = tk.Label(footer, text="● OFFLINE", bg="#0a0a0f", fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.footer_status.pack(side="left", padx=25, pady=8)
        
        tk.Label(footer, text=f"{APP_NAME} {APP_VERSION}", bg="#0a0a0f", fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="right", padx=25)

    def setup_hotkeys(self):
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Escape>", lambda e: self.stop())

    # ============================================================
    # LOGIC: STATIONS GRID
    # ============================================================
    def populate_stations(self):
        # Очистка
        for w in self.station_grid.winfo_children(): w.destroy()
        self.station_tiles.clear()
        
        col, row, cols = 0, 0, 2 # 2 колонки
        
        for name in self.filtered_stations:
            tile = self._create_tile(name)
            tile.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.station_grid.columnconfigure(col, weight=1)
            
            col += 1
            if col >= cols: col, row = 0, row + 1

    def _create_tile(self, name):
        # Основная рамка плитки
        frame = tk.Frame(self.station_grid, bg=PANEL_LIGHT, cursor="hand2", bd=0)
        
        # Внутренний контент
        content = tk.Frame(frame, bg=PANEL_LIGHT)
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        icon = tk.Label(content, text="📻", bg=PANEL_LIGHT, fg=ACCENT, font=("Segoe UI Emoji", 20))
        icon.pack(side="left", padx=(0, 12))
        
        label = tk.Label(content, text=name, bg=PANEL_LIGHT, fg="white", font=("Segoe UI", 9, "bold"), anchor="w", wraplength=130)
        label.pack(side="left", fill="x", expand=True)
        
        # Hover Effects
        def on_enter(e):
            if self.current_station != name:
                frame.configure(bg=ACCENT); content.configure(bg=ACCENT)
                icon.configure(bg=ACCENT, fg="white"); label.configure(bg=ACCENT, fg="white")
                
        def on_leave(e):
            if self.current_station != name:
                frame.configure(bg=PANEL_LIGHT); content.configure(bg=PANEL_LIGHT)
                icon.configure(bg=PANEL_LIGHT, fg=ACCENT); label.configure(bg=PANEL_LIGHT, fg="white")
                
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        frame.bind("<Button-1>", lambda e, n=name: self.select_station(n))
        
        self.station_tiles[name] = {"frame": frame, "content": content, "icon": icon, "label": label}
        return frame

    def select_station(self, name):
        self.current_station = name
        url = STATIONS.get(name)
        if not url: return self.player_error("URL не найден")
            
        self.current_url = url
        self.station_title_label.config(text=name)
        self.track_label.config(text="")
        self.set_status("● Подключение...", WARNING)
        self.footer_status.config(text="● CONNECTING", fg=WARNING)
        self.play_btn.config(text="⏸ PAUSE")
        
        # Обновляем вид всех плиток
        for s_name, widgets in self.station_tiles.items():
            is_active = (s_name == name)
            bg_color = ACCENT if is_active else PANEL_LIGHT
            fg_color = "white" if is_active else ACCENT
            
            widgets["frame"].configure(bg=bg_color)
            widgets["content"].configure(bg=bg_color)
            widgets["icon"].configure(bg=bg_color, fg=fg_color)
            widgets["label"].configure(bg=bg_color, fg="white")

        try: self.player.play(name, url)
        except Exception as exc: self.player_error(str(exc))

    def on_search(self, e=None):
        self.filtered_stations = search_stations(self.search_var.get())
        self.populate_stations()

    # ============================================================
    # LOGIC: PLAYBACK
    # ============================================================
    def toggle_play(self):
        if not self.current_station:
            if self.filtered_stations: self.select_station(self.filtered_stations[0])
            return
            
        state = self.player.get_state()
        if state == "PLAYING": self.player.pause()
        elif state == "PAUSED": self.player.resume()
        elif state in ("STOPPED", "ERROR", "ENDED"):
            if self.current_url: self.player.play(self.current_station, self.current_url)

    def stop(self):
        try: self.player.stop()
        except: pass
        self.play_btn.config(text="▶ PLAY")
        self.set_status("● Остановлено", TEXT_MUTED)
        self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)

    def player_state_changed(self, state):
        if self.closing: return
        status_map = {
            "PLAYING": ("● Сейчас играет", SUCCESS, "● LIVE", SUCCESS, "⏸ PAUSE"),
            "PAUSED": ("● Пауза", TEXT_MUTED, "● PAUSED", TEXT_MUTED, "▶ RESUME"),
            "ERROR": ("● Ошибка потока", ERROR, "● ERROR", ERROR, "▶ PLAY"),
            "STOPPED": ("● Остановлено", TEXT_MUTED, "● OFFLINE", TEXT_MUTED, "▶ PLAY"),
            "CONNECTING": ("● Буферизация...", WARNING, "● CONNECTING", WARNING, "⏸ PAUSE"),
        }
        
        if state in status_map:
            txt, clr, f_txt, f_clr, btn_txt = status_map[state]
            self.set_status(txt, clr)
            self.footer_status.config(text=f_txt, fg=f_clr)
            self.play_btn.config(text=btn_txt)

    def player_error(self, text):
        self.set_status("● Ошибка подключения", ERROR)
        self.footer_status.config(text="● ERROR", fg=ERROR)

    def set_status(self, text, color):
        try: self.status_label.config(text=text, fg=color)
        except: pass

    # ============================================================
    # LOGIC: VOLUME & LOOP
    # ============================================================
    def volume_changed(self, val):
        if self.updating_volume: return
        val = max(0, min(100, int(float(val))))
        self.player.set_volume(val)
        self.update_volume_icon(val)

    def update_volume_icon(self, val):
        icons = {0: "", 30: "", 60: "", 100: ""}
        icon = "🔊"
        for threshold, i in sorted(icons.items()):
            if val >= threshold and i: icon = i
        try: self.vol_icon.config(text=icon)
        except: pass

    def update_loop(self):
        if self.closing: return
        try:
            if self.player.get_state() == "PLAYING":
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
            
            title = self.player.get_title()
            if title: self.track_label.config(text=f"♪ {title}")
        except: pass
        
        try: self.root.after(UI_UPDATE_INTERVAL, self.update_loop)
        except: pass

    def on_closing(self):
        self.closing = True
        try: self.player.destroy()
        except: pass
        try: self.root.destroy()
        except: pass