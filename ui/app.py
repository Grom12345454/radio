# ui/app.py
import sys
import os
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *
from stations import get_categories, get_stations_by_category, search_stations
from player import RadioPlayer

class RadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # State
        self.current_station_name = None
        self.current_url = None
        self.closing = False
        self.updating_volume = False
        
        # Current View State
        self.current_category = None 
        self.displayed_stations = {} 

        # Player
        self.player = RadioPlayer()
        self.player.set_callbacks(
            on_state_changed=self.player_state_changed,
            on_error=self.player_error,
        )

        self.setup_styles()
        self.setup_ui()
        self.setup_hotkeys()

        # Init Volume
        self.updating_volume = True
        try:
            self.volume_scale.set(DEFAULT_VOLUME)
        finally:
            self.updating_volume = False
        self.player.set_volume(DEFAULT_VOLUME)
        self.update_volume_icon(DEFAULT_VOLUME)
        
        # Start Loop
        self.update_loop()

    def setup_styles(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass

        style.configure("Modern.TButton", background=ACCENT, foreground="white", borderwidth=0, padding=(18, 10), font=("Segoe UI", 10, "bold"))
        style.map("Modern.TButton", background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)])
        
        style.configure("Secondary.TButton", background=PANEL_LIGHT, foreground=TEXT, borderwidth=0, padding=(15, 10), font=("Segoe UI", 10))
        style.map("Secondary.TButton", background=[("active", PANEL_HOVER), ("pressed", PANEL_HOVER)])

    def setup_ui(self):
        # HEADER
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 14))
        
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text=APP_NAME, bg=BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Internet radio player", bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        # MAIN AREA
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=5)

        # LEFT PANEL (Categories / Stations)
        self.left_panel = tk.Frame(main, bg=PANEL, width=310)
        self.left_panel.pack(side="left", fill="y", padx=(0, 12))
        self.left_panel.pack_propagate(False)

        # Header for Left Panel (Dynamic Title)
        self.left_title_label = tk.Label(self.left_panel, text="КАТЕГОРИИ", bg=PANEL, fg=ACCENT, font=("Segoe UI", 11, "bold"))
        self.left_title_label.pack(anchor="w", padx=18, pady=(18, 10))

        # Search Box
        search_box = tk.Frame(self.left_panel, bg=PANEL_LIGHT)
        search_box.pack(fill="x", padx=14, pady=(0, 12))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_box, textvariable=self.search_var, bg=PANEL_LIGHT, fg=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 10))
        self.search_entry.pack(fill="x", padx=10, pady=9)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Content Area (Scrollable)
        self.content_frame = tk.Frame(self.left_panel, bg=PANEL)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        # Canvas & Scrollbar for content
        self.canvas = tk.Canvas(self.content_frame, bg=PANEL, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=PANEL)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel to scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Initial Render
        self.render_categories()

        # RIGHT PANEL (Player Info)
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Station Card
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

        # Controls
        controls = tk.Frame(right, bg=PANEL_LIGHT)
        controls.pack(fill="x", side="bottom")

        button_box = tk.Frame(controls, bg=PANEL_LIGHT)
        button_box.pack(side="left", padx=15, pady=12)

        self.play_button = ttk.Button(button_box, text="▶  PLAY", style="Modern.TButton", command=self.toggle_play)
        self.play_button.pack(side="left", padx=4)

        self.stop_button = ttk.Button(button_box, text="■  STOP", style="Secondary.TButton", command=self.stop)
        self.stop_button.pack(side="left", padx=4)

        volume_box = tk.Frame(controls, bg=PANEL_LIGHT)
        volume_box.pack(side="right", padx=18)

        self.volume_icon = tk.Label(volume_box, text="", bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI Emoji", 12))
        self.volume_icon.pack(side="left", padx=(0, 6))

        self.volume_scale = tk.Scale(volume_box, from_=0, to=100, orient="horizontal", length=140, showvalue=False, bg=PANEL_LIGHT, fg=TEXT, troughcolor="#303540", activebackground=ACCENT, highlightthickness=0, borderwidth=0, relief="flat", sliderrelief="flat", sliderlength=18, width=10, command=self.volume_changed)
        self.volume_scale.pack(side="left")

        # Footer
        footer = tk.Frame(self.root, bg=PANEL_LIGHT, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.footer_status = tk.Label(footer, text="● OFFLINE", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 8))
        self.footer_status.pack(side="left", padx=15, pady=5)
        tk.Label(footer, text=f"{APP_NAME} {APP_VERSION}", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(side="right", padx=15)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # --- RENDER LOGIC ---

    def clear_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def render_categories(self):
        self.current_category = None
        self.left_title_label.config(text="КАТЕГОРИИ", fg=ACCENT)
        self.clear_content()
        
        categories = get_categories()
        for cat in categories:
            btn = tk.Button(
                self.scrollable_frame,
                text=cat,
                bg=PANEL_LIGHT,
                fg=TEXT,
                activebackground=PANEL_HOVER,
                activeforeground=TEXT,
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                padx=15,
                pady=12,
                command=lambda c=cat: self.open_category(c)
            )
            btn.pack(fill="x", pady=4, padx=4)
            
            # Hover effect simulation
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=PANEL_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=PANEL_LIGHT))

    def open_category(self, category_name):
        self.current_category = category_name
        self.left_title_label.config(text=f"◀ {category_name}", fg=TEXT)
        self.clear_content()
        
        # Back Button
        back_btn = tk.Button(
            self.scrollable_frame,
            text="← Назад к категориям",
            bg=PANEL,
            fg=ACCENT,
            activebackground=PANEL,
            activeforeground=ACCENT_HOVER,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
            anchor="w",
            padx=0,
            pady=5,
            command=self.render_categories
        )
        back_btn.pack(fill="x", pady=(0, 10))

        stations = get_stations_by_category(category_name)
        self.displayed_stations = stations
        
        for name, url in stations.items():
            frame = tk.Frame(self.scrollable_frame, bg=PANEL_LIGHT)
            frame.pack(fill="x", pady=3, padx=4)
            
            lbl = tk.Label(frame, text=name, bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI", 10), anchor="w", padx=10, pady=8)
            lbl.pack(fill="x")
            
            # Play action
            frame.bind("<Button-1>", lambda e, n=name, u=url: self.play_station(n, u))
            lbl.bind("<Button-1>", lambda e, n=name, u=url: self.play_station(n, u))
            
            # Hover
            frame.bind("<Enter>", lambda e, f=frame: f.config(bg=PANEL_HOVER))
            frame.bind("<Leave>", lambda e, f=frame: f.config(bg=PANEL_LIGHT))
            lbl.bind("<Enter>", lambda e, f=frame: f.config(bg=PANEL_HOVER))
            lbl.bind("<Leave>", lambda e, f=frame: f.config(bg=PANEL_LIGHT))

    def play_station(self, name, url):
        self.current_station_name = name
        self.current_url = url
        self.station_title.config(text=name)
        self.track.config(text="")
        self.set_status("● Подключение...", WARNING)
        self.footer_status.config(text="● CONNECTING", fg=WARNING)
        self.play_button.config(text="⏸  PAUSE")
        
        try:
            self.player.play(name, url)
        except Exception as exc:
            self.player_error(str(exc))

    # --- SEARCH ---
    def on_search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            if self.current_category:
                self.open_category(self.current_category)
            else:
                self.render_categories()
            return
            
        self.left_title_label.config(text="РЕЗУЛЬТАТЫ ПОИСКА", fg=ACCENT)
        self.clear_content()
        
        results = search_stations(query)
        if not results:
            tk.Label(self.scrollable_frame, text="Ничего не найдено", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(pady=20)
            return
            
        # Find URLs for search results
        from stations import STATIONS
        found_data = {}
        for cat, st_list in STATIONS.items():
            for s_name, s_url in st_list.items():
                if s_name in results:
                    found_data[s_name] = s_url
                    
        self.displayed_stations = found_data
        
        for name, url in found_data.items():
             frame = tk.Frame(self.scrollable_frame, bg=PANEL_LIGHT)
             frame.pack(fill="x", pady=3, padx=4)
             lbl = tk.Label(frame, text=name, bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI", 10), anchor="w", padx=10, pady=8)
             lbl.pack(fill="x")
             frame.bind("<Button-1>", lambda e, n=name, u=url: self.play_station(n, u))
             lbl.bind("<Button-1>", lambda e, n=name, u=url: self.play_station(n, u))
             frame.bind("<Enter>", lambda e, f=frame: f.config(bg=PANEL_HOVER))
             frame.bind("<Leave>", lambda e, f=frame: f.config(bg=PANEL_LIGHT))
             lbl.bind("<Enter>", lambda e, f=frame: f.config(bg=PANEL_HOVER))
             lbl.bind("<Leave>", lambda e, f=frame: f.config(bg=PANEL_LIGHT))

    # --- PLAYER CONTROLS ---
    def toggle_play(self):
        if not self.current_station_name:
            return
        state = self.player.get_state()
        if state == "PLAYING": self.player.pause()
        elif state == "PAUSED": self.player.resume()
        elif state in ("STOPPED", "ERROR", "ENDED"):
            if self.current_url:
                self.set_status("● Подключение...", WARNING)
                self.player.play(self.current_station_name, self.current_url)
        else: self.player.resume()

    def stop(self):
        try: self.player.stop()
        except: pass
        self.play_button.config(text="▶  PLAY")
        self.set_status("● Остановлено", TEXT_MUTED)
        self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
        self.track.config(text="")

    def player_state_changed(self, state):
        if self.closing: return
        try:
            if state == "CONNECTING":
                self.set_status("● Подключение...", WARNING); self.footer_status.config(text="● CONNECTING", fg=WARNING); self.play_button.config(text="⏸  PAUSE")
            elif state == "PLAYING":
                self.set_status("● Сейчас играет", SUCCESS); self.footer_status.config(text="● LIVE", fg=SUCCESS); self.play_button.config(text="⏸  PAUSE")
            elif state == "PAUSED":
                self.set_status("● Пауза", TEXT_MUTED); self.footer_status.config(text="● PAUSED", fg=TEXT_MUTED); self.play_button.config(text="▶  RESUME")
            elif state == "STOPPED":
                self.set_status("● Остановлено", TEXT_MUTED); self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED); self.play_button.config(text="▶  PLAY")
            elif state == "ERROR":
                self.set_status("● Ошибка", ERROR); self.footer_status.config(text="● ERROR", fg=ERROR); self.play_button.config(text="▶  PLAY")
        except tk.TclError: pass

    def player_error(self, text):
        if self.closing: return
        self.set_status("● Ошибка подключения", ERROR)
        try:
            self.footer_status.config(text="● ERROR", fg=ERROR); self.play_button.config(text="▶  PLAY")
        except tk.TclError: pass

    def set_status(self, text, color):
        try: self.status.config(text=text, fg=color)
        except tk.TclError: pass

    def volume_changed(self, value):
        if self.updating_volume: return
        try:
            value = max(0, min(100, int(float(value))))
            self.player.set_volume(value)
            self.update_volume_icon(value)
        except: pass

    def change_volume(self, amount):
        try:
            current = self.player.get_volume()
            value = max(0, min(100, current + amount))
            self.player.set_volume(value)
            self.updating_volume = True
            try: self.volume_scale.set(value)
            finally: self.updating_volume = False
            self.update_volume_icon(value)
        except: pass

    def update_volume_icon(self, value):
        try:
            v = int(value)
            icon = "🔇" if v <= 0 else "" if v < 40 else "" if v < 75 else ""
            self.volume_icon.config(text=icon)
        except: pass

    def setup_hotkeys(self):
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Escape>", lambda e: self.stop())
        self.root.bind("<Up>", lambda e: self.change_volume(5))
        self.root.bind("<Down>", lambda e: self.change_volume(-5))

    def update_loop(self):
        if self.closing: return
        try:
            state = self.player.get_state()
            if state == "PLAYING": self.footer_status.config(text="● LIVE", fg=SUCCESS)
            title = self.player.get_title()
            if title: self.track.config(text=f"♪ {title}")
        except: pass
        try: self.root.after(UI_UPDATE_INTERVAL, self.update_loop)
        except: pass

    def on_closing(self):
        if self.closing: return
        self.closing = True
        try: self.player.destroy()
        except: pass
        try: self.root.destroy()
        except: pass