# ============================================================
# ui/app.py
# RadioStation 3D
# Professional Desktop Player
# Radio + YouTube
# ============================================================

import os
import sys
import math
import random
import tkinter as tk
from tkinter import ttk

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ============================================================
# PROJECT
# ============================================================

from config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    DEFAULT_VOLUME,
    UI_UPDATE_INTERVAL,
)

from stations import (
    STATIONS,
    get_categories,
    get_stations_by_category,
    search_stations,
)

from player import RadioPlayer


class RadioApp:

    # ========================================================
    # COLORS
    # ========================================================

    BG = "#080B12"
    BG_2 = "#0B0F18"

    SIDEBAR = "#0D121C"

    SURFACE = "#111722"
    SURFACE_2 = "#151C29"
    SURFACE_3 = "#1B2433"

    BORDER = "#202A3A"
    BORDER_LIGHT = "#2B374B"

    TEXT = "#F5F7FB"
    TEXT_SECONDARY = "#B6C0D0"
    TEXT_MUTED = "#6F7B8F"

    ACCENT = "#6D7CFF"
    ACCENT_HOVER = "#8290FF"
    ACCENT_DARK = "#3E4CA8"

    SUCCESS = "#31D17C"
    WARNING = "#F2B84B"
    ERROR = "#FF5F6D"

    WHITE = "#FFFFFF"

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self, root):

        self.root = root

        self.closing = False

        self.root.title(
            f"{APP_NAME}  •  {APP_VERSION}"
        )

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.minsize(
            MIN_WIDTH,
            MIN_HEIGHT,
        )

        self.root.configure(
            bg=self.BG
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_closing
        )

        # ====================================================
        # STATE
        # ====================================================

        self.current_station_name = None
        self.current_url = None
        self.current_category = None

        self.current_view = "home"

        self.favorite_stations = set()
        self.history = []

        self.displayed_stations = {}

        self.last_state = None
        self.last_title = None

        self.search_after_id = None
        self.update_after_id = None
        self.wave_after_id = None

        self.updating_volume = False

        self.wave_phase = 0.0

        # ====================================================
        # PLAYER
        # ====================================================

        self.player = RadioPlayer()

        self.player.set_callbacks(
            on_state_changed=self._player_state_callback,
            on_error=self._player_error_callback,
            on_metadata_changed=self._player_metadata_callback,
        )

        # ====================================================
        # UI
        # ====================================================

        self.setup_ttk()

        self.build_interface()

        self.setup_hotkeys()

        self.initialize_volume()

        self.render_home()

        self.update_loop()

        self.animate_waveform()

    # ========================================================
    # TTK
    # ========================================================

    def setup_ttk(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Radio.Horizontal.TScale",
            troughcolor=self.SURFACE_3,
            background=self.ACCENT,
            bordercolor=self.SURFACE_3,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
        )

        style.configure(
            "Radio.Vertical.TScrollbar",
            background=self.SURFACE_3,
            troughcolor=self.SURFACE,
            borderwidth=0,
            arrowcolor=self.TEXT_MUTED,
        )

    # ========================================================
    # MAIN UI
    # ========================================================

    def build_interface(self):

        # ====================================================
        # HEADER
        # ====================================================

        self.header = tk.Frame(
            self.root,
            bg=self.BG,
            height=72,
        )

        self.header.pack(
            fill="x",
            padx=24,
            pady=(16, 8),
        )

        self.header.pack_propagate(False)

        # ----------------------------------------------------
        # BRAND
        # ----------------------------------------------------

        brand = tk.Frame(
            self.header,
            bg=self.BG,
        )

        brand.pack(
            side="left",
            fill="y",
        )

        logo = tk.Canvas(
            brand,
            width=38,
            height=38,
            bg=self.BG,
            highlightthickness=0,
        )

        logo.pack(
            side="left",
            pady=8,
        )

        logo.create_oval(
            4,
            4,
            34,
            34,
            fill=self.ACCENT,
            outline="",
        )

        logo.create_oval(
            11,
            11,
            27,
            27,
            fill=self.BG,
            outline="",
        )

        logo.create_oval(
            16,
            16,
            22,
            22,
            fill=self.ACCENT,
            outline="",
        )

        brand_text = tk.Frame(
            brand,
            bg=self.BG,
        )

        brand_text.pack(
            side="left",
            padx=(10, 0),
        )

        tk.Label(
            brand_text,
            text="RADIOSTATION 3D",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 14, "bold"),
        ).pack(
            anchor="w"
        )

        tk.Label(
            brand_text,
            text="INTERNET RADIO • MUSIC PLAYER",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_outer = tk.Frame(
            self.header,
            bg=self.BORDER,
        )

        search_outer.pack(
            side="left",
            fill="x",
            expand=True,
            padx=50,
            ipady=1,
        )

        search = tk.Frame(
            search_outer,
            bg=self.SURFACE,
        )

        search.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            search,
            text="⌕",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 18),
        ).pack(
            side="left",
            padx=(14, 4),
        )

        self.search_var = tk.StringVar()

        self.search_entry = tk.Entry(
            search,
            textvariable=self.search_var,
            bg=self.SURFACE,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        self.search_entry.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 14),
        )

        self.search_entry.insert(
            0,
            "Search stations..."
        )

        self.search_entry.configure(
            fg=self.TEXT_MUTED
        )

        self.search_entry.bind(
            "<FocusIn>",
            self.search_focus_in
        )

        self.search_entry.bind(
            "<FocusOut>",
            self.search_focus_out
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.on_search
        )

        # ====================================================
        # BODY
        # ====================================================

        body = tk.Frame(
            self.root,
            bg=self.BG,
        )

        body.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=(0, 12),
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = tk.Frame(
            body,
            bg=self.SIDEBAR,
            width=220,
        )

        self.sidebar.pack(
            side="left",
            fill="y",
        )

        self.sidebar.pack_propagate(False)

        self.build_sidebar()

        # ====================================================
        # CONTENT
        # ====================================================

        content = tk.Frame(
            body,
            bg=self.BG,
        )

        content.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(14, 0),
        )

        # ----------------------------------------------------
        # NOW PLAYING
        # ----------------------------------------------------

        self.now_playing = tk.Frame(
            content,
            bg=self.SURFACE,
            height=205,
        )

        self.now_playing.pack(
            fill="x",
        )

        self.now_playing.pack_propagate(False)

        self.build_now_playing()

        # ----------------------------------------------------
        # STATION SECTION
        # ----------------------------------------------------

        self.station_header = tk.Frame(
            content,
            bg=self.BG,
            height=54,
        )

        self.station_header.pack(
            fill="x",
            pady=(12, 0),
        )

        self.station_header.pack_propagate(False)

        self.section_title = tk.Label(
            self.station_header,
            text="Stations",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 16, "bold"),
        )

        self.section_title.pack(
            side="left",
            pady=8,
        )

        self.section_count = tk.Label(
            self.station_header,
            text="",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 9),
        )

        self.section_count.pack(
            side="left",
            padx=12,
        )

        # ----------------------------------------------------
        # SCROLL
        # ----------------------------------------------------

        station_outer = tk.Frame(
            content,
            bg=self.BG,
        )

        station_outer.pack(
            fill="both",
            expand=True,
        )

        self.canvas = tk.Canvas(
            station_outer,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )

        self.scrollbar = ttk.Scrollbar(
            station_outer,
            orient="vertical",
            command=self.canvas.yview,
            style="Radio.Vertical.TScrollbar",
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.cards_frame = tk.Frame(
            self.canvas,
            bg=self.BG,
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.cards_frame,
            anchor="nw",
        )

        self.cards_frame.bind(
            "<Configure>",
            self.on_cards_configure
        )

        self.canvas.bind(
            "<Configure>",
            self.on_canvas_configure
        )

        # ====================================================
        # PLAYER BAR
        # ====================================================

        self.build_player_bar()

    # ========================================================
    # SIDEBAR
    # ========================================================

    def build_sidebar(self):

        tk.Label(
            self.sidebar,
            text="LIBRARY",
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 10),
        )

        self.add_sidebar_button(
            "⌂",
            "Home",
            lambda: self.show_view("home"),
        )

        self.add_sidebar_button(
            "★",
            "Favorites",
            lambda: self.show_view("favorites"),
        )

        self.add_sidebar_button(
            "◷",
            "History",
            lambda: self.show_view("history"),
        )

        tk.Label(
            self.sidebar,
            text="GENRES",
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            padx=20,
            pady=(24, 10),
        )

        for category in get_categories():

            self.add_sidebar_button(
                "•",
                category,
                lambda c=category: self.show_category(c),
            )

    def add_sidebar_button(
        self,
        icon,
        text,
        command,
    ):

        button = tk.Frame(
            self.sidebar,
            bg=self.SIDEBAR,
            cursor="hand2",
            height=40,
        )

        button.pack(
            fill="x",
            padx=10,
            pady=2,
        )

        button.pack_propagate(False)

        icon_label = tk.Label(
            button,
            text=icon,
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 12),
        )

        icon_label.pack(
            side="left",
            padx=(10, 10),
        )

        text_label = tk.Label(
            button,
            text=text,
            bg=self.SIDEBAR,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 9),
        )

        text_label.pack(
            side="left",
        )

        for widget in (
            button,
            icon_label,
            text_label,
        ):
            widget.bind(
                "<Button-1>",
                lambda event: command()
            )

            widget.bind(
                "<Enter>",
                lambda event, b=button:
                self.sidebar_hover(b, True)
            )

            widget.bind(
                "<Leave>",
                lambda event, b=button:
                self.sidebar_hover(b, False)
            )

    def sidebar_hover(self, widget, active):

        widget.configure(
            bg=self.SURFACE_2
            if active
            else self.SIDEBAR
        )

        for child in widget.winfo_children():

            child.configure(
                bg=self.SURFACE_2
                if active
                else self.SIDEBAR
            )

    # ========================================================
    # NOW PLAYING
    # ========================================================

    def build_now_playing(self):

        # ----------------------------------------------------
        # COVER
        # ----------------------------------------------------

        self.cover_canvas = tk.Canvas(
            self.now_playing,
            width=150,
            height=150,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        self.cover_canvas.pack(
            side="left",
            padx=(26, 20),
            pady=25,
        )

        self.draw_cover()

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        info = tk.Frame(
            self.now_playing,
            bg=self.SURFACE,
        )

        info.pack(
            side="left",
            fill="both",
            expand=True,
            pady=25,
        )

        self.live_label = tk.Label(
            info,
            text="●  READY",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        )

        self.live_label.pack(
            anchor="w"
        )

        self.now_station_label = tk.Label(
            info,
            text="Nothing playing",
            bg=self.SURFACE,
            fg=self.TEXT,
            font=("Segoe UI", 23, "bold"),
        )

        self.now_station_label.pack(
            anchor="w",
            pady=(5, 2),
        )

        self.now_title_label = tk.Label(
            info,
            text="Choose a station to start listening",
            bg=self.SURFACE,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 10),
        )

        self.now_title_label.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # WAVEFORM
        # ----------------------------------------------------

        self.wave_canvas = tk.Canvas(
            info,
            width=360,
            height=44,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        self.wave_canvas.pack(
            anchor="w",
            pady=(18, 0),
        )

        self.wave_bars = []

        for i in range(30):

            x = 4 + i * 11

            bar = self.wave_canvas.create_rectangle(
                x,
                20,
                x + 5,
                24,
                fill=self.ACCENT,
                outline="",
            )

            self.wave_bars.append(bar)

        # ----------------------------------------------------
        # RIGHT STATUS
        # ----------------------------------------------------

        right = tk.Frame(
            self.now_playing,
            bg=self.SURFACE,
            width=180,
        )

        right.pack(
            side="right",
            fill="y",
            padx=24,
            pady=25,
        )

        right.pack_propagate(False)

        tk.Label(
            right,
            text="SOURCE",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="e"
        )

        self.source_label = tk.Label(
            right,
            text="—",
            bg=self.SURFACE,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 9),
        )

        self.source_label.pack(
            anchor="e",
            pady=(4, 0),
        )

    # ========================================================
    # COVER
    # ========================================================

    def draw_cover(self):

        canvas = self.cover_canvas

        canvas.delete("all")

        canvas.create_oval(
            8,
            8,
            142,
            142,
            fill=self.ACCENT_DARK,
            outline="",
        )

        canvas.create_oval(
            20,
            20,
            130,
            130,
            fill=self.SURFACE_2,
            outline=self.ACCENT,
            width=2,
        )

        canvas.create_oval(
            48,
            48,
            102,
            102,
            fill=self.ACCENT,
            outline="",
        )

        canvas.create_oval(
            65,
            65,
            85,
            85,
            fill=self.SURFACE,
            outline="",
        )

        canvas.create_text(
            75,
            117,
            text="♫",
            fill=self.TEXT,
            font=("Segoe UI", 17, "bold"),
        )

    # ========================================================
    # PLAYER BAR
    # ========================================================

    def build_player_bar(self):

        self.player_bar = tk.Frame(
            self.root,
            bg=self.SURFACE,
            height=84,
        )

        self.player_bar.pack(
            fill="x",
            padx=24,
            pady=(0, 16),
        )

        self.player_bar.pack_propagate(False)

        # ----------------------------------------------------
        # CURRENT
        # ----------------------------------------------------

        current = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
            width=250,
        )

        current.pack(
            side="left",
            fill="y",
            padx=18,
        )

        current.pack_propagate(False)

        self.bottom_station = tk.Label(
            current,
            text="Nothing playing",
            bg=self.SURFACE,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        )

        self.bottom_station.pack(
            anchor="w",
            pady=(20, 0),
        )

        self.bottom_title = tk.Label(
            current,
            text="—",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8),
        )

        self.bottom_title.pack(
            anchor="w",
            pady=(2, 0),
        )

        # ----------------------------------------------------
        # CONTROLS
        # ----------------------------------------------------

        controls = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
        )

        controls.pack(
            side="left",
            expand=True,
        )

        self.stop_button = self.make_control_button(
            controls,
            "■",
            self.stop,
            30,
        )

        self.stop_button.pack(
            side="left",
            padx=6,
        )

        self.prev_button = self.make_control_button(
            controls,
            "↶",
            self.previous_station,
            30,
        )

        self.prev_button.pack(
            side="left",
            padx=6,
        )

        self.play_button = tk.Button(
            controls,
            text="▶",
            command=self.toggle_play,
            bg=self.ACCENT,
            fg=self.WHITE,
            activebackground=self.ACCENT_HOVER,
            activeforeground=self.WHITE,
            relief="flat",
            bd=0,
            width=4,
            height=1,
            font=("Segoe UI", 14, "bold"),
            cursor="hand2",
        )

        self.play_button.pack(
            side="left",
            padx=8,
        )

        self.next_button = self.make_control_button(
            controls,
            "↷",
            self.next_station,
            30,
        )

        self.next_button.pack(
            side="left",
            padx=6,
        )

        self.random_button = self.make_control_button(
            controls,
            "⤨",
            self.random_station,
            30,
        )

        self.random_button.pack(
            side="left",
            padx=6,
        )

        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        volume = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
            width=250,
        )

        volume.pack(
            side="right",
            fill="y",
            padx=18,
        )

        volume.pack_propagate(False)

        self.volume_icon = tk.Label(
            volume,
            text="🔊",
            bg=self.SURFACE,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 11),
            cursor="hand2",
        )

        self.volume_icon.pack(
            side="left",
            pady=27,
        )

        self.volume_icon.bind(
            "<Button-1>",
            lambda event: self.toggle_mute()
        )

        self.volume_var = tk.DoubleVar(
            value=DEFAULT_VOLUME
        )

        self.volume_scale = ttk.Scale(
            volume,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.volume_changed,
            style="Radio.Horizontal.TScale",
        )

        self.volume_scale.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 8),
            pady=28,
        )

        self.volume_label = tk.Label(
            volume,
            text=f"{DEFAULT_VOLUME}%",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8),
            width=4,
        )

        self.volume_label.pack(
            side="right",
            pady=28,
        )

    # ========================================================
    # BUTTON
    # ========================================================

    def make_control_button(
        self,
        parent,
        text,
        command,
        width,
    ):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.SURFACE,
            fg=self.TEXT_SECONDARY,
            activebackground=self.SURFACE_3,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            width=width // 10,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
        )

    # ========================================================
    # VIEWS
    # ========================================================

    def show_view(self, view):

        self.current_view = view

        if view == "home":
            self.render_home()

        elif view == "favorites":
            self.render_favorites()

        elif view == "history":
            self.render_history()

    def show_category(self, category):

        self.current_category = category
        self.current_view = "category"

        self.section_title.configure(
            text=category
        )

        self.render_stations(
            get_stations_by_category(category)
        )

    def render_home(self):

        self.current_category = None

        all_stations = {}

        for category, stations in STATIONS.items():

            for name, url in stations.items():

                all_stations[name] = url

        self.section_title.configure(
            text="All Stations"
        )

        self.render_stations(
            all_stations
        )

    def render_favorites(self):

        stations = {}

        for category, category_stations in STATIONS.items():

            for name, url in category_stations.items():

                if name in self.favorite_stations:
                    stations[name] = url

        self.section_title.configure(
            text="Favorites"
        )

        self.render_stations(
            stations
        )

    def render_history(self):

        stations = {}

        for name in reversed(self.history):

            url = self.find_station_url(name)

            if url:
                stations[name] = url

        self.section_title.configure(
            text="Recently Played"
        )

        self.render_stations(
            stations
        )

    # ========================================================
    # STATIONS
    # ========================================================

    def render_stations(self, stations):

        for child in self.cards_frame.winfo_children():
            child.destroy()

        self.displayed_stations = dict(
            stations
        )

        count = len(stations)

        self.section_count.configure(
            text=f"{count} stations"
        )

        if not stations:

            empty = tk.Frame(
                self.cards_frame,
                bg=self.BG,
                height=180,
            )

            empty.pack(
                fill="x",
                pady=30,
            )

            tk.Label(
                empty,
                text="Nothing here yet",
                bg=self.BG,
                fg=self.TEXT,
                font=("Segoe UI", 15, "bold"),
            ).pack(
                pady=(50, 5)
            )

            tk.Label(
                empty,
                text="Choose another category or station.",
                bg=self.BG,
                fg=self.TEXT_MUTED,
                font=("Segoe UI", 9),
            ).pack()

            return

        columns = 3

        for index, (name, url) in enumerate(
            stations.items()
        ):

            row = index // columns
            column = index % columns

            self.create_station_card(
                name,
                url,
                row,
                column,
            )

        for column in range(columns):

            self.cards_frame.grid_columnconfigure(
                column,
                weight=1,
            )

    # ========================================================
    # STATION CARD
    # ========================================================

    def create_station_card(
        self,
        name,
        url,
        row,
        column,
    ):

        card = tk.Frame(
            self.cards_frame,
            bg=self.SURFACE,
            height=125,
            cursor="hand2",
        )

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=5,
            pady=5,
        )

        card.grid_propagate(False)

        # ----------------------------------------------------
        # Icon
        # ----------------------------------------------------

        icon = tk.Canvas(
            card,
            width=58,
            height=58,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        icon.pack(
            side="left",
            padx=(14, 10),
            pady=30,
        )

        icon.create_oval(
            4,
            4,
            54,
            54,
            fill=self.ACCENT_DARK,
            outline="",
        )

        icon.create_text(
            29,
            29,
            text="♫",
            fill=self.WHITE,
            font=("Segoe UI", 18, "bold"),
        )

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

        text_frame = tk.Frame(
            card,
            bg=self.SURFACE,
        )

        text_frame.pack(
            side="left",
            fill="both",
            expand=True,
            pady=22,
        )

        title = tk.Label(
            text_frame,
            text=name,
            bg=self.SURFACE,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )

        title.pack(
            anchor="w",
        )

        source = (
            "YOUTUBE"
            if self.player.is_youtube_url(url)
            else "RADIO"
        )

        source_label = tk.Label(
            text_frame,
            text=source,
            bg=self.SURFACE,
            fg=self.ACCENT
            if source == "YOUTUBE"
            else self.TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
        )

        source_label.pack(
            anchor="w",
            pady=(5, 0),
        )

        # ----------------------------------------------------
        # Favorite
        # ----------------------------------------------------

        favorite = tk.Label(
            card,
            text="★"
            if name in self.favorite_stations
            else "☆",
            bg=self.SURFACE,
            fg=self.WARNING
            if name in self.favorite_stations
            else self.TEXT_MUTED,
            font=("Segoe UI", 14),
            cursor="hand2",
        )

        favorite.pack(
            side="right",
            padx=12,
        )

        favorite.bind(
            "<Button-1>",
            lambda event, n=name:
            self.toggle_favorite(n)
        )

        # ----------------------------------------------------
        # Click
        # ----------------------------------------------------

        for widget in (
            card,
            icon,
            text_frame,
            title,
            source_label,
        ):

            widget.bind(
                "<Button-1>",
                lambda event,
                n=name,
                u=url:
                self.play_station(n, u)
            )

            widget.bind(
                "<Enter>",
                lambda event,
                c=card:
                self.card_hover(c, True)
            )

            widget.bind(
                "<Leave>",
                lambda event,
                c=card:
                self.card_hover(c, False)
            )

    # ========================================================
    # CARD HOVER
    # ========================================================

    def card_hover(self, card, active):

        color = (
            self.SURFACE_2
            if active
            else self.SURFACE
        )

        card.configure(
            bg=color
        )

        for child in card.winfo_children():

            try:
                child.configure(
                    bg=color
                )
            except Exception:
                pass

            for subchild in child.winfo_children():

                try:
                    subchild.configure(
                        bg=color
                    )
                except Exception:
                    pass

    # ========================================================
    # PLAY STATION
    # ========================================================

    def play_station(
        self,
        station_name,
        url,
    ):

        if not url:
            return

        self.current_station_name = station_name
        self.current_url = url

        self.now_station_label.configure(
            text=station_name
        )

        self.bottom_station.configure(
            text=station_name
        )

        self.bottom_title.configure(
            text="Connecting..."
        )

        self.now_title_label.configure(
            text="Connecting..."
        )

        source = (
            "YouTube"
            if self.player.is_youtube_url(url)
            else "Internet Radio"
        )

        self.source_label.configure(
            text=source
        )

        self.live_label.configure(
            text="●  CONNECTING",
            fg=self.WARNING,
        )

        # History
        if station_name in self.history:
            self.history.remove(
                station_name
            )

        self.history.append(
            station_name
        )

        self.history = self.history[-50:]

        success = self.player.play(
            station_name,
            url,
        )

        if success:

            self.play_button.configure(
                text="Ⅱ"
            )

    # ========================================================
    # PLAY / PAUSE
    # ========================================================

    def toggle_play(self):

        state = self.player.get_state()

        if state == "PAUSED":

            self.player.resume()
            return

        if state in (
            "PLAYING",
            "BUFFERING",
            "CONNECTING",
        ):

            self.player.pause()
            return

        if self.current_station_name and self.current_url:

            self.player.play(
                self.current_station_name,
                self.current_url,
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self.player.stop()

        self.play_button.configure(
            text="▶"
        )

        self.live_label.configure(
            text="●  READY",
            fg=self.TEXT_MUTED,
        )

    # ========================================================
    # RANDOM
    # ========================================================

    def random_station(self):

        stations = []

        for category in STATIONS.values():

            for name, url in category.items():

                stations.append(
                    (name, url)
                )

        if not stations:
            return

        name, url = random.choice(
            stations
        )

        self.play_station(
            name,
            url,
        )

    # ========================================================
    # NEXT / PREVIOUS
    # ========================================================

    def get_all_stations(self):

        result = []

        for category in STATIONS.values():

            for name, url in category.items():

                result.append(
                    (name, url)
                )

        return result

    def next_station(self):

        stations = self.get_all_stations()

        if not stations:
            return

        current = self.current_station_name

        if not current:
            self.play_station(
                *stations[0]
            )
            return

        names = [
            item[0]
            for item in stations
        ]

        if current not in names:
            self.play_station(
                *stations[0]
            )
            return

        index = names.index(current)

        index = (
            index + 1
        ) % len(stations)

        self.play_station(
            *stations[index]
        )

    def previous_station(self):

        stations = self.get_all_stations()

        if not stations:
            return

        current = self.current_station_name

        if not current:
            self.play_station(
                *stations[-1]
            )
            return

        names = [
            item[0]
            for item in stations
        ]

        if current not in names:
            self.play_station(
                *stations[-1]
            )
            return

        index = names.index(current)

        index = (
            index - 1
        ) % len(stations)

        self.play_station(
            *stations[index]
        )

    # ========================================================
    # FAVORITES
    # ========================================================

    def toggle_favorite(self, name):

        if name in self.favorite_stations:

            self.favorite_stations.remove(
                name
            )

        else:

            self.favorite_stations.add(
                name
            )

        # Обновляем текущий экран.
        if self.current_view == "favorites":
            self.render_favorites()

        elif self.current_view == "category":
            self.show_category(
                self.current_category
            )

        elif self.current_view == "home":
            self.render_home()

    # Alias для совместимости
    toggle_station_favorite = toggle_favorite

    # ========================================================
    # FIND URL
    # ========================================================

    def find_station_url(self, station_name):

        for stations in STATIONS.values():

            if station_name in stations:
                return stations[station_name]

        return None

    # ========================================================
    # SEARCH
    # ========================================================

    def search_focus_in(self, event):

        if (
            self.search_entry.get()
            == "Search stations..."
        ):

            self.search_entry.delete(
                0,
                tk.END,
            )

            self.search_entry.configure(
                fg=self.TEXT
            )

    def search_focus_out(self, event):

        if not self.search_entry.get():

            self.search_entry.insert(
                0,
                "Search stations..."
            )

            self.search_entry.configure(
                fg=self.TEXT_MUTED
            )

    def on_search(self, event=None):

        if self.search_after_id:

            try:
                self.root.after_cancel(
                    self.search_after_id
                )
            except Exception:
                pass

        self.search_after_id = self.root.after(
            150,
            self.perform_search,
        )

    def perform_search(self):

        query = self.search_entry.get().strip()

        if (
            not query
            or query == "Search stations..."
        ):

            self.render_home()
            return

        results = {}

        for category, stations in STATIONS.items():

            for name, url in stations.items():

                if query.lower() in name.lower():

                    results[name] = url

        self.current_view = "search"

        self.section_title.configure(
            text=f"Search: {query}"
        )

        self.render_stations(
            results
        )

    # ========================================================
    # VOLUME
    # ========================================================

    def initialize_volume(self):

        self.volume_var.set(
            self.player.get_volume()
        )

        self.update_volume_ui(
            self.player.get_volume()
        )

    def volume_changed(self, value):

        if self.updating_volume:
            return

        try:
            volume = int(float(value))
        except Exception:
            return

        self.player.set_volume(
            volume
        )

        self.update_volume_ui(
            volume
        )

    def update_volume_ui(self, volume):

        volume = max(
            0,
            min(100, int(volume))
        )

        self.volume_label.configure(
            text=f"{volume}%"
        )

        if volume <= 0:

            self.volume_icon.configure(
                text="🔇"
            )

        elif volume < 50:

            self.volume_icon.configure(
                text="🔉"
            )

        else:

            self.volume_icon.configure(
                text="🔊"
            )

    def toggle_mute(self):

        muted = self.player.toggle_mute()

        if muted:

            self.volume_icon.configure(
                text="🔇"
            )

        else:

            self.update_volume_ui(
                self.player.get_volume()
            )

    # ========================================================
    # PLAYER CALLBACKS
    # ========================================================

    def _player_state_callback(self, state):

        if self.closing:
            return

        self.root.after(
            0,
            lambda s=state:
            self.player_state_changed(s)
        )

    def _player_error_callback(self, message):

        if self.closing:
            return

        self.root.after(
            0,
            lambda m=message:
            self.player_error(m)
        )

    def _player_metadata_callback(self, title):

        if self.closing:
            return

        self.root.after(
            0,
            lambda t=title:
            self.player_metadata_changed(t)
        )

    # ========================================================
    # STATE UI
    # ========================================================

    def player_state_changed(self, state):

        if self.closing:
            return

        self.last_state = state

        if state == "PLAYING":

            self.live_label.configure(
                text="●  LIVE",
                fg=self.SUCCESS,
            )

            self.play_button.configure(
                text="Ⅱ"
            )

        elif state == "PAUSED":

            self.live_label.configure(
                text="●  PAUSED",
                fg=self.WARNING,
            )

            self.play_button.configure(
                text="▶"
            )

        elif state == "BUFFERING":

            self.live_label.configure(
                text="●  BUFFERING",
                fg=self.WARNING,
            )

            self.play_button.configure(
                text="Ⅱ"
            )

        elif state == "CONNECTING":

            self.live_label.configure(
                text="●  CONNECTING",
                fg=self.WARNING,
            )

            self.play_button.configure(
                text="Ⅱ"
            )

        elif state == "RECONNECTING":

            self.live_label.configure(
                text="●  RECONNECTING",
                fg=self.WARNING,
            )

            self.play_button.configure(
                text="Ⅱ"
            )

        elif state == "STOPPED":

            self.live_label.configure(
                text="●  READY",
                fg=self.TEXT_MUTED,
            )

            self.play_button.configure(
                text="▶"
            )

        elif state == "ENDED":

            self.live_label.configure(
                text="●  ENDED",
                fg=self.TEXT_MUTED,
            )

            self.play_button.configure(
                text="▶"
            )

        elif state == "ERROR":

            self.live_label.configure(
                text="●  ERROR",
                fg=self.ERROR,
            )

            self.play_button.configure(
                text="▶"
            )

    # ========================================================
    # METADATA
    # ========================================================

    def player_metadata_changed(self, title):

        if not title:
            return

        self.last_title = title

        self.now_title_label.configure(
            text=title
        )

        self.bottom_title.configure(
            text=title
        )

    # ========================================================
    # ERROR
    # ========================================================

    def player_error(self, message):

        if self.closing:
            return

        self.live_label.configure(
            text="●  ERROR",
            fg=self.ERROR,
        )

        self.bottom_title.configure(
            text="Playback error"
        )

        self.now_title_label.configure(
            text=str(message)
        )

    # ========================================================
    # WAVEFORM
    # ========================================================

    def animate_waveform(self):

        if self.closing:
            return

        playing = self.player.get_state() in (
            "PLAYING",
            "BUFFERING",
            "CONNECTING",
        )

        self.wave_phase += 0.22

        for index, bar in enumerate(
            self.wave_bars
        ):

            if playing:

                value = (
                    math.sin(
                        self.wave_phase
                        + index * 0.55
                    )
                    + 1
                ) / 2

                height = 5 + int(
                    value * 25
                )

            else:

                height = 4

            center = 22

            self.wave_canvas.coords(
                bar,
                4 + index * 11,
                center - height,
                9 + index * 11,
                center + height,
            )

        self.wave_after_id = self.root.after(
            70,
            self.animate_waveform,
        )

    # ========================================================
    # UPDATE LOOP
    # ========================================================

    def update_loop(self):

        if self.closing:
            return

        try:

            state = self.player.get_state()

            if state != self.last_state:

                self.player_state_changed(
                    state
                )

            station = (
                self.player.get_current_station()
            )

            if station:
                self.current_station_name = station

        except Exception:
            pass

        self.update_after_id = self.root.after(
            max(50, UI_UPDATE_INTERVAL),
            self.update_loop,
        )

    # ========================================================
    # CANVAS
    # ========================================================

    def on_cards_configure(self, event=None):

        try:

            self.canvas.configure(
                scrollregion=self.canvas.bbox(
                    "all"
                )
            )

        except Exception:
            pass

    def on_canvas_configure(self, event):

        try:

            self.canvas.itemconfigure(
                self.canvas_window,
                width=event.width,
            )

        except Exception:
            pass

    # ========================================================
    # HOTKEYS
    # ========================================================

    def setup_hotkeys(self):

        self.root.bind(
            "<space>",
            lambda event:
            self.toggle_play()
        )

        self.root.bind(
            "<Control-f>",
            lambda event:
            self.focus_search()
        )

        self.root.bind(
            "<Escape>",
            lambda event:
            self.clear_search()
        )

        self.root.bind(
            "<Left>",
            lambda event:
            self.previous_station()
        )

        self.root.bind(
            "<Right>",
            lambda event:
            self.next_station()
        )

    def focus_search(self):

        self.search_entry.focus_set()

        self.search_entry.select_range(
            0,
            tk.END,
        )

    def clear_search(self):

        self.search_entry.delete(
            0,
            tk.END,
        )

        self.render_home()

    # ========================================================
    # CLOSE
    # ========================================================

    def on_closing(self):

        if self.closing:
            return

        self.closing = True

        if self.search_after_id:

            try:
                self.root.after_cancel(
                    self.search_after_id
                )
            except Exception:
                pass

        if self.update_after_id:

            try:
                self.root.after_cancel(
                    self.update_after_id
                )
            except Exception:
                pass

        if self.wave_after_id:

            try:
                self.root.after_cancel(
                    self.wave_after_id
                )
            except Exception:
                pass

        try:
            self.player.destroy()
        except Exception:
            pass

        self.root.destroy()