import tkinter as tk
from tkinter import ttk
from config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    DEFAULT_VOLUME,
    UI_UPDATE_INTERVAL,
    ACCENT,
    ACCENT_HOVER,
    BG,
    PANEL,
    PANEL_LIGHT,
    PANEL_HOVER,
    TEXT,
    TEXT_MUTED,
    SUCCESS,
    WARNING,
    ERROR,
)
from stations import STATIONS, search_stations
from player import RadioPlayer
from visualizer import Visualizer


class RadioApp:
    def __init__(self, root):
        self.root = root
        
        # --------------------------------------------------------
        # WINDOW
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
        self.station_tiles = {}  # Словарь для хранения виджетов плиток

        # --------------------------------------------------------
        # PLAYER
        # --------------------------------------------------------
        self.player = RadioPlayer()
        self.player.set_callbacks(
            on_state_changed=self.player_state_changed,
            on_error=self.player_error,
        )

        # --------------------------------------------------------
        # UI
        # --------------------------------------------------------
        self.setup_styles()
        self.setup_ui()
        self.setup_hotkeys()

        # --------------------------------------------------------
        # INITIAL VOLUME
        # --------------------------------------------------------
        self.updating_volume = True
        try:
            self.volume_scale.set(DEFAULT_VOLUME)
        finally:
            self.updating_volume = False
        self.player.set_volume(DEFAULT_VOLUME)
        self.update_volume_icon(DEFAULT_VOLUME)

        # --------------------------------------------------------
        # VISUALIZER
        # --------------------------------------------------------
        self.visualizer = Visualizer(self.visualizer_canvas, ACCENT)

        # --------------------------------------------------------
        # UPDATE LOOP
        # --------------------------------------------------------
        self.update_loop()

    # ============================================================
    # STYLES
    # ============================================================
    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Modern.TButton",
            background=ACCENT,
            foreground="white",
            borderwidth=0,
            padding=(18, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Modern.TButton",
            background=[
                ("active", ACCENT_HOVER),
                ("pressed", ACCENT_HOVER),
            ],
        )

        style.configure(
            "Secondary.TButton",
            background=PANEL_LIGHT,
            foreground=TEXT,
            borderwidth=0,
            padding=(15, 10),
            font=("Segoe UI", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[
                ("active", PANEL_HOVER),
                ("pressed", PANEL_HOVER),
            ],
        )

    # ============================================================
    # UI SETUP
    # ============================================================
    def setup_ui(self):
        # HEADER
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 14))

        tk.Label(header, text="", bg=BG, fg=TEXT, font=("Segoe UI Emoji", 30)).pack(side="left", padx=(0, 12))

        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")

        tk.Label(title_box, text=APP_NAME, bg=BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Internet radio player", bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        # MAIN CONTAINER
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=5)

        # LEFT PANEL (STATIONS)
        left = tk.Frame(main, bg=PANEL, width=360)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        tk.Label(left, text="РАДИОСТАНЦИИ", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(
            anchor="w", padx=18, pady=(18, 10)
        )

        # SEARCH BAR
        search_box = tk.Frame(left, bg=PANEL_LIGHT)
        search_box.pack(fill="x", padx=14, pady=(0, 12))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_box,
            textvariable=self.search_var,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.search_entry.pack(fill="x", padx=10, pady=9)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # STATION GRID (SCROLLABLE CANVAS)
        list_frame = tk.Frame(left, bg=PANEL)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        scrollbar = tk.Scrollbar(list_frame, bg=PANEL_LIGHT, troughcolor=PANEL, activebackground=ACCENT, relief="flat", borderwidth=0)
        scrollbar.pack(side="right", fill="y")

        self.station_canvas = tk.Canvas(list_frame, bg=PANEL, highlightthickness=0, yscrollcommand=scrollbar.set)
        self.station_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.station_canvas.yview)

        self.station_grid_container = tk.Frame(self.station_canvas, bg=PANEL)
        self.station_canvas.create_window((0, 0), window=self.station_grid_container, anchor="nw")

        self.station_grid_container.bind("<Configure>", lambda e: self.station_canvas.configure(scrollregion=self.station_canvas.bbox("all")))
        self.station_canvas.bind_all("<MouseWheel>", lambda e: self.station_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # RIGHT PANEL
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # CURRENT STATION CARD
        station_card = tk.Frame(right, bg=PANEL, height=180)
        station_card.pack(fill="x", pady=(0, 12))
        station_card.pack_propagate(False)

        self.cover = tk.Canvas(station_card, width=130, height=130, bg=PANEL_LIGHT, highlightthickness=0)
        self.cover.pack(side="left", padx=22, pady=22)
        self.cover.create_text(65, 65, text="♪", fill=ACCENT, font=("Segoe UI", 48, "bold"))

        info = tk.Frame(station_card, bg=PANEL)
        info.pack(side="left", fill="both", expand=True, padx=(0, 20))

        self.station_title = tk.Label(info, text="Выберите станцию", bg=PANEL, fg=TEXT, font=("Segoe UI", 18, "bold"), wraplength=500, justify="left")
        self.station_title.pack(anchor="w", pady=(30, 6))

        self.status = tk.Label(info, text="● Готов к воспроизведению", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 10))
        self.status.pack(anchor="w")

        self.track = tk.Label(info, text="", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.track.pack(anchor="w", pady=(12, 0))

        # VISUALIZER
        visual = tk.Frame(right, bg=PANEL)
        visual.pack(fill="both", expand=True, pady=(0, 12))

        tk.Label(visual, text="AUDIO", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(12, 3))

        self.visualizer_canvas = tk.Canvas(visual, bg=PANEL, highlightthickness=0)
        self.visualizer_canvas.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # CONTROLS
        controls = tk.Frame(right, bg=PANEL_LIGHT)
        controls.pack(fill="x")

        button_box = tk.Frame(controls, bg=PANEL_LIGHT)
        button_box.pack(side="left", padx=15, pady=12)

        self.play_button = ttk.Button(button_box, text="▶ PLAY", style="Modern.TButton", command=self.toggle_play)
        self.play_button.pack(side="left", padx=4)

        self.stop_button = ttk.Button(button_box, text="■ STOP", style="Secondary.TButton", command=self.stop)
        self.stop_button.pack(side="left", padx=4)

        volume_box = tk.Frame(controls, bg=PANEL_LIGHT)
        volume_box.pack(side="right", padx=18)

        self.volume_icon = tk.Label(volume_box, text="🔊", bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI Emoji", 12))
        self.volume_icon.pack(side="left", padx=(0, 6))

        self.volume_scale = tk.Scale(
            volume_box, from_=0, to=100, orient="horizontal", length=140, showvalue=False,
            bg=PANEL_LIGHT, fg=TEXT, troughcolor="#303540", activebackground=ACCENT,
            highlightthickness=0, borderwidth=0, relief="flat", sliderrelief="flat",
            sliderlength=18, width=10, command=self.volume_changed,
        )
        self.volume_scale.pack(side="left")

        # FOOTER
        footer = tk.Frame(self.root, bg=PANEL_LIGHT, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.footer_status = tk.Label(footer, text="● OFFLINE", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 8))
        self.footer_status.pack(side="left", padx=15, pady=5)

        tk.Label(footer, text=f"{APP_NAME} {APP_VERSION}", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(side="right", padx=15)

    # ============================================================
    # HOTKEYS
    # ============================================================
    def setup_hotkeys(self):
        self.root.bind("<space>", lambda event: self.toggle_play())
        self.root.bind("<Escape>", lambda event: self.stop())
        self.root.bind("<Up>", lambda event: self.change_volume(5))
        self.root.bind("<Down>", lambda event: self.change_volume(-5))

    # ============================================================
    # STATION GRID LOGIC
    # ============================================================
    def populate_stations(self):
        for widget in self.station_grid_container.winfo_children():
            widget.destroy()
        self.station_tiles.clear()

        col = 0
        row = 0
        cols = 2

        for station_name in self.filtered_stations:
            tile = self._create_station_tile(station_name)
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.station_grid_container.columnconfigure(col, weight=1)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _create_station_tile(self, name):
        frame = tk.Frame(self.station_grid_container, bg=PANEL_LIGHT, cursor="hand2")
        
        icon = tk.Label(frame, text="", bg=PANEL_LIGHT, fg=ACCENT, font=("Segoe UI Emoji", 16))
        icon.pack(side="left", padx=(10, 8), pady=10)
        
        label = tk.Label(frame, text=name, bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI", 9, "bold"), anchor="w", wraplength=130)
        label.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        
        # Hover effects
        frame.bind("<Enter>", lambda e, f=frame: f.configure(bg=PANEL_HOVER))
        frame.bind("<Leave>", lambda e, f=frame, n=name: self._reset_tile(f, n))
        frame.bind("<Button-1>", lambda e, n=name: self._select_station(n))
        
        # Store reference
        self.station_tiles[name] = {"frame": frame, "icon": icon, "label": label}
        return frame

    def _reset_tile(self, frame, name):
        if self.current_station != name:
            frame.configure(bg=PANEL_LIGHT)

    def _select_station(self, name):
        self.current_station = name
        url = STATIONS.get(name)
        if not url:
            self.player_error("URL станции не найден")
            return
            
        self.current_url = url
        self.station_title.config(text=name)
        self.track.config(text="")
        self.set_status("● Подключение...", WARNING)
        self.footer_status.config(text="● CONNECTING", fg=WARNING)
        self.play_button.config(text="⏸ PAUSE")
        
        # Update grid visuals
        for s_name, widgets in self.station_tiles.items():
            is_active = (s_name == name)
            bg_color = ACCENT if is_active else PANEL_LIGHT
            fg_color = "white" if is_active else ACCENT
            text_color = "white" if is_active else TEXT
            
            widgets["frame"].configure(bg=bg_color)
            widgets["icon"].configure(fg=fg_color)
            widgets["label"].configure(fg=text_color)

        try:
            self.player.play(name, url)
        except Exception as exc:
            self.player_error(str(exc))

    # ============================================================
    # SEARCH & PLAY
    # ============================================================
    def on_search(self, event=None):
        query = self.search_var.get()
        self.filtered_stations = search_stations(query)
        self.populate_stations()

    def play_selected(self):
        # Для обратной совместимости с хоткеями, если нужно
        if self.current_station:
            self._select_station(self.current_station)

    # ============================================================
    # PLAYBACK CONTROLS
    # ============================================================
    def toggle_play(self):
        if not self.current_station:
            if self.filtered_stations:
                self._select_station(self.filtered_stations[0])
            return

        state = self.player.get_state()
        if state == "PLAYING":
            self.player.pause()
        elif state == "PAUSED":
            self.player.resume()
        elif state in ("STOPPED", "ERROR", "ENDED"):
            if self.current_url:
                self.set_status("● Подключение...", WARNING)
                self.player.play(self.current_station, self.current_url)
            else:
                self.player.resume()

    def stop(self):
        try:
            self.player.stop()
        except Exception:
            pass
        self.play_button.config(text="▶ PLAY")
        self.set_status("● Остановлено", TEXT_MUTED)
        self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
        self.track.config(text="")

    # ============================================================
    # PLAYER EVENTS
    # ============================================================
    def player_state_changed(self, state):
        if self.closing:
            return
        try:
            if state == "CONNECTING":
                self.set_status("● Подключение...", WARNING)
                self.footer_status.config(text="● CONNECTING", fg=WARNING)
                self.play_button.config(text="⏸ PAUSE")
            elif state == "PLAYING":
                self.set_status("● Сейчас играет", SUCCESS)
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
                self.play_button.config(text="⏸ PAUSE")
            elif state == "PAUSED":
                self.set_status("● Пауза", TEXT_MUTED)
                self.footer_status.config(text="● PAUSED", fg=TEXT_MUTED)
                self.play_button.config(text="▶ RESUME")
            elif state == "STOPPED":
                self.set_status("● Остановлено", TEXT_MUTED)
                self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
                self.play_button.config(text="▶ PLAY")
            elif state == "ERROR":
                self.set_status("● Ошибка", ERROR)
                self.footer_status.config(text="● ERROR", fg=ERROR)
                self.play_button.config(text="▶ PLAY")
            elif state == "ENDED":
                self.set_status("● Поток завершён", TEXT_MUTED)
                self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
                self.play_button.config(text="▶ PLAY")
        except tk.TclError:
            pass

    def player_error(self, text):
        if self.closing:
            return
        self.set_status("● Ошибка подключения", ERROR)
        try:
            self.footer_status.config(text="● ERROR", fg=ERROR)
            self.play_button.config(text="▶ PLAY")
        except tk.TclError:
            pass

    def set_status(self, text, color):
        try:
            self.status.config(text=text, fg=color)
        except tk.TclError:
            pass

    # ============================================================
    # VOLUME
    # ============================================================
    def volume_changed(self, value):
        if self.updating_volume:
            return
        try:
            value = int(float(value))
            value = max(0, min(100, value))
            self.player.set_volume(value)
            self.update_volume_icon(value)
        except (ValueError, TypeError, tk.TclError):
            pass

    def change_volume(self, amount):
        try:
            current = self.player.get_volume()
            value = max(0, min(100, current + amount))
            self.player.set_volume(value)
            self.updating_volume = True
            try:
                self.volume_scale.set(value)
            finally:
                self.updating_volume = False
            self.update_volume_icon(value)
        except (ValueError, TypeError, tk.TclError):
            pass

    def update_volume_icon(self, value):
        try:
            value = int(value)
            if value <= 0:
                self.volume_icon.config(text="🔇")
            elif value < 40:
                self.volume_icon.config(text="")
            elif value < 75:
                self.volume_icon.config(text="🔉")
            else:
                self.volume_icon.config(text="🔊")
        except (ValueError, TypeError, tk.TclError):
            pass

    # ============================================================
    # UPDATE LOOP
    # ============================================================
    def update_loop(self):
        if self.closing:
            return
        try:
            state = self.player.get_state()
            if state == "PLAYING":
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
            
            title = self.player.get_title()
            if title:
                self.track.config(text=f"♪ {title}")
            
            if hasattr(self, "visualizer"):
                self.visualizer.draw(active=(state == "PLAYING"))
        except tk.TclError:
            return
        except Exception:
            pass

        try:
            self.root.after(UI_UPDATE_INTERVAL, self.update_loop)
        except tk.TclError:
            pass

    # ============================================================
    # CLOSE
    # ============================================================
    def on_closing(self):
        if self.closing:
            return
        self.closing = True
        try:
            self.player.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass