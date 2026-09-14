# ============================================================
# ui/app.py
# RadioStation 3D - Professional Player UI
# ============================================================

import os
import sys
import math
import random
import tkinter as tk
from tkinter import ttk


# ------------------------------------------------------------
# Project root
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    """
    Professional dark radio player UI.

    Совместим с:
        stations.py
        config.py
        player.py
        main.py

    Никаких дополнительных UI-библиотек не требуется.
    """

    # ========================================================
    # DESIGN SYSTEM
    # ========================================================

    BG = "#080B12"
    BG_2 = "#0B0F18"

    SIDEBAR = "#0D121C"

    SURFACE = "#111722"
    SURFACE_2 = "#151C29"
    SURFACE_3 = "#1B2433"

    BORDER = "#202A3A"
    BORDER_LIGHT = "#273246"

    TEXT = "#F5F7FB"
    TEXT_SECONDARY = "#B6C0D0"
    TEXT_MUTED = "#6F7B8F"

    ACCENT = "#6D7CFF"
    ACCENT_HOVER = "#8190FF"
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

        # ----------------------------------------------------
        # Application state
        # ----------------------------------------------------

        self.current_station_name = None
        self.current_url = None
        self.current_category = None

        self.favorite_stations = set()
        self.history = []

        self.displayed_stations = {}

        self.search_placeholder = "Search stations..."

        self.search_after_id = None

        self.ui_after_ids = []

        self.updating_volume = False

        self.last_state = None
        self.last_title = None

        self.current_view = "home"

        # ----------------------------------------------------
        # Player
        # ----------------------------------------------------

        self.player = RadioPlayer()

        # Callback'и VLC могут приходить из другого потока.
        # Поэтому НЕ меняем Tkinter напрямую.
        if hasattr(
            self.player,
            "set_callbacks"
        ):

            self.player.set_callbacks(
                on_state_changed=self._player_state_callback,
                on_error=self._player_error_callback,
                on_metadata_changed=self._player_metadata_callback,
            )

        # ----------------------------------------------------
        # Build UI
        # ----------------------------------------------------

        self.setup_ttk()

        self.build_interface()

        self.setup_hotkeys()

        self.initialize_volume()

        self.update_loop()

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
    # MAIN INTERFACE
    # ========================================================

    def build_interface(self):

        # ====================================================
        # TOP HEADER
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
        # Brand
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

        # logo ring
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
            text="INTERNET RADIO",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # Search
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
            fg=self.TEXT_MUTED,
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
            padx=(0, 12),
            pady=8,
        )

        self.search_entry.insert(
            0,
            self.search_placeholder
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

        # ----------------------------------------------------
        # Live indicator
        # ----------------------------------------------------

        self.live_indicator = tk.Frame(
            self.header,
            bg=self.SURFACE,
        )

        self.live_indicator.pack(
            side="right",
            padx=(12, 0),
        )

        self.live_dot = tk.Label(
            self.live_indicator,
            text="●",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 9),
        )

        self.live_dot.pack(
            side="left",
            padx=(10, 3),
            pady=7,
        )

        self.live_text = tk.Label(
            self.live_indicator,
            text="OFFLINE",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        )

        self.live_text.pack(
            side="left",
            padx=(0, 10),
            pady=7,
        )

        # ====================================================
        # BODY
        # ====================================================

        self.body = tk.Frame(
            self.root,
            bg=self.BG,
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=(0, 12),
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = tk.Frame(
            self.body,
            bg=self.SIDEBAR,
            width=210,
        )

        self.sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 14),
        )

        self.sidebar.pack_propagate(False)

        self.build_sidebar()

        # ====================================================
        # MAIN
        # ====================================================

        self.main = tk.Frame(
            self.body,
            bg=self.BG,
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True,
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        self.canvas = tk.Canvas(
            self.main,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )

        self.scrollbar = ttk.Scrollbar(
            self.main,
            orient="vertical",
            command=self.canvas.yview,
            style="Radio.Vertical.TScrollbar",
        )

        self.scroll_content = tk.Frame(
            self.canvas,
            bg=self.BG,
        )

        self.canvas_window = self.canvas.create_window(
            0,
            0,
            window=self.scroll_content,
            anchor="nw",
        )

        self.scroll_content.bind(
            "<Configure>",
            self.on_scroll_content_configure
        )

        self.canvas.bind(
            "<Configure>",
            self.on_canvas_configure
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self.on_mousewheel
        )

        # ====================================================
        # NOW PLAYING
        # ====================================================

        self.build_now_playing()

        # ====================================================
        # STATIONS
        # ====================================================

        self.build_station_section()

        # ====================================================
        # BOTTOM PLAYER
        # ====================================================

        self.build_player_bar()

    # ========================================================
    # SIDEBAR
    # ========================================================

    def build_sidebar(self):

        # title
        tk.Label(
            self.sidebar,
            text="LIBRARY",
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            padx=18,
            pady=(20, 9),
        )

        self.home_button = self.sidebar_button(
            "⌂   Home",
            self.render_home,
        )

        self.favorites_button = self.sidebar_button(
            "★   Favorites",
            self.show_favorites,
        )

        self.history_button = self.sidebar_button(
            "◷   History",
            self.show_history,
        )

        tk.Label(
            self.sidebar,
            text="GENRES",
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            padx=18,
            pady=(26, 9),
        )

        self.category_buttons = []

        for category in get_categories():

            button = self.sidebar_button(
                category,
                lambda c=category: self.open_category(c),
            )

            self.category_buttons.append(
                (category, button)
            )

        # bottom info
        bottom = tk.Frame(
            self.sidebar,
            bg=self.SIDEBAR,
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=18,
            pady=18,
        )

        tk.Frame(
            bottom,
            bg=self.BORDER,
            height=1,
        ).pack(
            fill="x",
            pady=(0, 12),
        )

        tk.Label(
            bottom,
            text="RADIOSTATION 3D",
            bg=self.SIDEBAR,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w"
        )

        tk.Label(
            bottom,
            text=f"Version {APP_VERSION}",
            bg=self.SIDEBAR,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7),
        ).pack(
            anchor="w"
        )

    def sidebar_button(
        self,
        text,
        command,
    ):

        button = tk.Label(
            self.sidebar,
            text=text,
            bg=self.SIDEBAR,
            fg=self.TEXT_SECONDARY,
            anchor="w",
            padx=14,
            pady=9,
            font=("Segoe UI", 9),
            cursor="hand2",
        )

        button.pack(
            fill="x",
            padx=7,
            pady=1,
        )

        button.bind(
            "<Button-1>",
            lambda e: command()
        )

        button.bind(
            "<Enter>",
            lambda e, b=button: b.config(
                bg=self.SURFACE_2,
                fg=self.TEXT,
            )
        )

        button.bind(
            "<Leave>",
            lambda e, b=button: b.config(
                bg=self.SIDEBAR,
                fg=self.TEXT_SECONDARY,
            )
        )

        return button

    # ========================================================
    # NOW PLAYING
    # ========================================================

    def build_now_playing(self):

        self.now_playing = tk.Frame(
            self.scroll_content,
            bg=self.SURFACE,
            height=330,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

        self.now_playing.pack(
            fill="x",
            pady=(0, 20),
        )

        self.now_playing.pack_propagate(False)

        # ----------------------------------------------------
        # Cover
        # ----------------------------------------------------

        self.cover = tk.Canvas(
            self.now_playing,
            width=240,
            height=240,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        self.cover.pack(
            side="left",
            padx=(28, 24),
            pady=34,
        )

        self.draw_cover(
            "RADIO",
            False,
        )

        # ----------------------------------------------------
        # Information
        # ----------------------------------------------------

        info = tk.Frame(
            self.now_playing,
            bg=self.SURFACE,
        )

        info.pack(
            side="left",
            fill="both",
            expand=True,
            pady=30,
        )

        tk.Label(
            info,
            text="NOW PLAYING",
            bg=self.SURFACE,
            fg=self.ACCENT,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w"
        )

        self.station_title = tk.Label(
            info,
            text="Select a station",
            bg=self.SURFACE,
            fg=self.TEXT,
            font=("Segoe UI", 25, "bold"),
            anchor="w",
        )

        self.station_title.pack(
            anchor="w",
            pady=(7, 0),
        )

        self.station_category = tk.Label(
            info,
            text="Internet Radio",
            bg=self.SURFACE,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 10),
        )

        self.station_category.pack(
            anchor="w",
            pady=(2, 0),
        )

        self.station_status = tk.Label(
            info,
            text="● Ready to play",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 9),
        )

        self.station_status.pack(
            anchor="w",
            pady=(13, 0),
        )

        # ----------------------------------------------------
        # Track information
        # ----------------------------------------------------

        track_box = tk.Frame(
            info,
            bg=self.SURFACE_2,
        )

        track_box.pack(
            fill="x",
            padx=(0, 28),
            pady=(20, 0),
        )

        self.track_label = tk.Label(
            track_box,
            text="♪  No track information",
            bg=self.SURFACE_2,
            fg=self.TEXT_SECONDARY,
            anchor="w",
            font=("Segoe UI", 9),
        )

        self.track_label.pack(
            fill="x",
            padx=13,
            pady=10,
        )

        # ----------------------------------------------------
        # Waveform
        # ----------------------------------------------------

        self.waveform = tk.Canvas(
            info,
            height=50,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        self.waveform.pack(
            fill="x",
            padx=(0, 28),
            pady=(14, 0),
        )

        self.wave_bars = []

        for _ in range(42):

            item = self.waveform.create_rectangle(
                0,
                0,
                0,
                0,
                fill=self.SURFACE_3,
                outline="",
            )

            self.wave_bars.append(item)

        # ----------------------------------------------------
        # Favorite
        # ----------------------------------------------------

        self.favorite_button = tk.Label(
            self.now_playing,
            text="☆",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 25),
            cursor="hand2",
        )

        self.favorite_button.place(
            relx=0.965,
            rely=0.08,
            anchor="ne",
        )

        self.favorite_button.bind(
            "<Button-1>",
            lambda e: self.toggle_favorite()
        )

        self.favorite_button.bind(
            "<Enter>",
            lambda e: self.favorite_button.config(
                fg=self.ACCENT
            )
        )

        self.favorite_button.bind(
            "<Leave>",
            lambda e: self.update_favorite_button()
        )

    # ========================================================
    # COVER
    # ========================================================

    def draw_cover(
        self,
        station_name,
        active,
    ):

        self.cover.delete("all")

        w = 240
        h = 240

        # shadow / base
        self.cover.create_rectangle(
            6,
            6,
            w - 6,
            h - 6,
            fill=self.SURFACE_2,
            outline=self.BORDER,
        )

        # outer ring
        self.cover.create_oval(
            28,
            28,
            212,
            212,
            fill=self.SURFACE_3,
            outline=(
                self.ACCENT
                if active
                else self.BORDER_LIGHT
            ),
            width=2,
        )

        # inner ring
        self.cover.create_oval(
            68,
            68,
            172,
            172,
            fill=self.BG,
            outline=(
                self.ACCENT_DARK
                if active
                else self.BORDER
            ),
            width=2,
        )

        # center
        self.cover.create_oval(
            96,
            96,
            144,
            144,
            fill=(
                self.ACCENT
                if active
                else self.SURFACE_3
            ),
            outline="",
        )

        self.cover.create_text(
            120,
            120,
            text="♪",
            fill=self.WHITE,
            font=("Segoe UI", 22, "bold"),
        )

        # name
        short_name = (
            station_name[:18]
            if station_name
            else "RADIO"
        )

        self.cover.create_text(
            120,
            202,
            text=short_name.upper(),
            fill=self.TEXT_SECONDARY,
            font=("Segoe UI", 7, "bold"),
        )

    # ========================================================
    # STATIONS SECTION
    # ========================================================

    def build_station_section(self):

        self.station_section = tk.Frame(
            self.scroll_content,
            bg=self.BG,
        )

        self.station_section.pack(
            fill="both",
            expand=True,
            pady=(0, 90),
        )

        header = tk.Frame(
            self.station_section,
            bg=self.BG,
        )

        header.pack(
            fill="x",
            pady=(0, 12),
        )

        self.section_title = tk.Label(
            header,
            text="Popular stations",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 16, "bold"),
        )

        self.section_title.pack(
            side="left"
        )

        self.section_count = tk.Label(
            header,
            text="",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8),
        )

        self.section_count.pack(
            side="left",
            padx=10,
            pady=4,
        )

        self.cards_frame = tk.Frame(
            self.station_section,
            bg=self.BG,
        )

        self.cards_frame.pack(
            fill="both",
            expand=True,
        )

        self.cards_frame.bind(
            "<Configure>",
            self.refresh_card_columns,
        )

        self.render_home()

    # ========================================================
    # HOME
    # ========================================================

    def render_home(self):

        self.current_view = "home"
        self.current_category = None

        self.section_title.config(
            text="Popular stations"
        )

        self.clear_cards()

        stations = {}

        for category, category_stations in STATIONS.items():

            for name, url in category_stations.items():

                if name not in stations:
                    stations[name] = (
                        url,
                        category,
                    )

        self.render_station_grid(
            stations
        )

    # ========================================================
    # CATEGORY
    # ========================================================

    def open_category(
        self,
        category,
    ):

        self.current_view = "category"
        self.current_category = category

        self.section_title.config(
            text=category.title()
        )

        self.clear_cards()

        category_stations = get_stations_by_category(
            category
        )

        stations = {
            name: (
                url,
                category,
            )
            for name, url in category_stations.items()
        }

        self.render_station_grid(
            stations
        )

    # ========================================================
    # GRID
    # ========================================================

    def calculate_columns(self):

        width = self.cards_frame.winfo_width()

        if width < 500:
            return 1

        if width < 800:
            return 2

        if width < 1100:
            return 3

        return 4

    def refresh_card_columns(
        self,
        event=None,
    ):

        if not self.displayed_stations:
            return

        self.render_station_grid(
            self.displayed_stations,
            rebuild=True,
        )

    def render_station_grid(
        self,
        stations,
        rebuild=True,
    ):

        self.displayed_stations = stations

        if rebuild:
            self.clear_cards()

        if not stations:
            self.show_empty_state()
            return

        columns = self.calculate_columns()

        self.section_count.config(
            text=f"{len(stations)} stations"
        )

        for index, (name, data) in enumerate(
            stations.items()
        ):

            if not rebuild:
                continue

            url, category = data

            card = self.create_station_card(
                name,
                url,
                category,
            )

            row = index // columns
            column = index % columns

            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=5,
                pady=5,
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
        category,
    ):

        card = tk.Frame(
            self.cards_frame,
            bg=self.SURFACE,
            height=185,
            cursor="hand2",
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

        card.pack_propagate(False)

        # ----------------------------------------------------
        # Top
        # ----------------------------------------------------

        top = tk.Frame(
            card,
            bg=self.SURFACE,
        )

        top.pack(
            fill="x",
            padx=12,
            pady=(12, 5),
        )

        logo = tk.Canvas(
            top,
            width=72,
            height=72,
            bg=self.SURFACE,
            highlightthickness=0,
        )

        logo.pack(
            side="left"
        )

        logo.create_rectangle(
            3,
            3,
            69,
            69,
            fill=self.SURFACE_2,
            outline=self.BORDER_LIGHT,
        )

        logo.create_text(
            36,
            36,
            text="♪",
            fill=self.ACCENT,
            font=("Segoe UI", 25, "bold"),
        )

        # favorite
        favorite = tk.Label(
            top,
            text=(
                "★"
                if name in self.favorite_stations
                else "☆"
            ),
            bg=self.SURFACE,
            fg=(
                self.ACCENT
                if name in self.favorite_stations
                else self.TEXT_MUTED
            ),
            font=("Segoe UI", 14),
            cursor="hand2",
        )

        favorite.pack(
            side="right",
            anchor="n",
        )

        favorite.bind(
            "<Button-1>",
            lambda e, n=name:
                self.toggle_station_favorite(n),
        )

        # ----------------------------------------------------
        # Name
        # ----------------------------------------------------

        title = tk.Label(
            card,
            text=name,
            bg=self.SURFACE,
            fg=self.TEXT,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )

        title.pack(
            fill="x",
            padx=13,
            pady=(2, 0),
        )

        subtitle = tk.Label(
            card,
            text=category,
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            anchor="w",
            font=("Segoe UI", 7),
        )

        subtitle.pack(
            fill="x",
            padx=13,
            pady=(2, 0),
        )

        # ----------------------------------------------------
        # Bottom
        # ----------------------------------------------------

        bottom = tk.Frame(
            card,
            bg=self.SURFACE,
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=13,
            pady=10,
        )

        live = tk.Label(
            bottom,
            text="● LIVE",
            bg=self.SURFACE,
            fg=self.SUCCESS,
            font=("Segoe UI", 7, "bold"),
        )

        live.pack(
            side="left"
        )

        play = tk.Label(
            bottom,
            text="PLAY  ›",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
        )

        play.pack(
            side="right"
        )

        # ----------------------------------------------------
        # Hover
        # ----------------------------------------------------

        widgets = [
            card,
            top,
            logo,
            title,
            subtitle,
            bottom,
            live,
        ]

        def enter(event=None):

            for widget in widgets:

                try:
                    widget.config(
                        bg=self.SURFACE_3
                    )
                except Exception:
                    pass

            play.config(
                bg=self.SURFACE_3,
                fg=self.ACCENT_HOVER,
            )

        def leave(event=None):

            for widget in widgets:

                try:
                    widget.config(
                        bg=self.SURFACE
                    )
                except Exception:
                    pass

            play.config(
                bg=self.SURFACE,
                fg=self.TEXT_MUTED,
            )

        def play_station(event=None):

            self.play_station(
                name,
                url,
            )

        for widget in widgets:

            widget.bind(
                "<Enter>",
                enter
            )

            widget.bind(
                "<Leave>",
                leave
            )

            widget.bind(
                "<Button-1>",
                play_station
            )

        play.bind(
            "<Button-1>",
            play_station
        )

        return card

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_cards(self):

        for widget in self.cards_frame.winfo_children():

            widget.destroy()

        self.displayed_stations = {}

    # ========================================================
    # EMPTY
    # ========================================================

    def show_empty_state(self):

        frame = tk.Frame(
            self.cards_frame,
            bg=self.BG,
        )

        frame.pack(
            fill="x",
            pady=60,
        )

        tk.Label(
            frame,
            text="○",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 32),
        ).pack()

        tk.Label(
            frame,
            text="Nothing here yet",
            bg=self.BG,
            fg=self.TEXT_SECONDARY,
            font=("Segoe UI", 11, "bold"),
        ).pack(
            pady=(8, 2)
        )

        tk.Label(
            frame,
            text="Choose another category or search for a station.",
            bg=self.BG,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack()

    # ========================================================
    # PLAYER BAR
    # ========================================================

    def build_player_bar(self):

        self.player_bar = tk.Frame(
            self.root,
            bg=self.SURFACE,
            height=78,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

        self.player_bar.pack(
            side="bottom",
            fill="x",
            padx=24,
            pady=(0, 14),
        )

        self.player_bar.pack_propagate(False)

        # ----------------------------------------------------
        # Station
        # ----------------------------------------------------

        current = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
        )

        current.pack(
            side="left",
            fill="y",
            padx=16,
        )

        self.player_station = tk.Label(
            current,
            text="Nothing playing",
            bg=self.SURFACE,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold"),
        )

        self.player_station.pack(
            anchor="w",
            pady=(15, 0),
        )

        self.player_track = tk.Label(
            current,
            text="Choose a station",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7),
        )

        self.player_track.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # Center controls
        # ----------------------------------------------------

        controls = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
        )

        controls.pack(
            side="left",
            padx=35,
        )

        self.stop_button = self.player_button(
            controls,
            "■",
            self.stop,
        )

        self.play_button = self.player_button(
            controls,
            "▶",
            self.toggle_play,
            primary=True,
        )

        self.random_button = self.player_button(
            controls,
            "↗",
            self.play_random,
        )

        # ----------------------------------------------------
        # Volume
        # ----------------------------------------------------

        volume = tk.Frame(
            self.player_bar,
            bg=self.SURFACE,
        )

        volume.pack(
            side="right",
            padx=18,
        )

        self.volume_label = tk.Label(
            volume,
            text="VOL",
            bg=self.SURFACE,
            fg=self.TEXT_MUTED,
            font=("Segoe UI", 7, "bold"),
        )

        self.volume_label.pack(
            side="left",
            padx=(0, 8),
        )

        self.volume_scale = tk.Scale(
            volume,
            from_=0,
            to=100,
            orient="horizontal",
            length=130,
            showvalue=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            troughcolor=self.SURFACE_3,
            activebackground=self.ACCENT,
            highlightthickness=0,
            bd=0,
            relief="flat",
            sliderrelief="flat",
            sliderlength=16,
            width=8,
            command=self.volume_changed,
        )

        self.volume_scale.pack(
            side="left"
        )

    def player_button(
        self,
        parent,
        text,
        command,
        primary=False,
    ):

        button = tk.Label(
            parent,
            text=text,
            width=3,
            pady=7,
            bg=(
                self.ACCENT
                if primary
                else self.SURFACE_2
            ),
            fg=self.TEXT,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
        )

        button.pack(
            side="left",
            padx=3,
        )

        normal = (
            self.ACCENT
            if primary
            else self.SURFACE_2
        )

        hover = (
            self.ACCENT_HOVER
            if primary
            else self.SURFACE_3
        )

        button.bind(
            "<Button-1>",
            lambda e: command()
        )

        button.bind(
            "<Enter>",
            lambda e: button.config(
                bg=hover
            )
        )

        button.bind(
            "<Leave>",
            lambda e: button.config(
                bg=normal
            )
        )

        return button

    # ========================================================
    # SEARCH
    # ========================================================

    def search_focus_in(self, event=None):

        if self.search_entry.get() == self.search_placeholder:

            self.search_entry.delete(
                0,
                "end"
            )

            self.search_entry.config(
                fg=self.TEXT
            )

    def search_focus_out(self, event=None):

        if not self.search_entry.get().strip():

            self.search_entry.insert(
                0,
                self.search_placeholder
            )

            self.search_entry.config(
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
            120,
            self.perform_search
        )

    def perform_search(self):

        query = self.search_entry.get().strip()

        if (
            not query
            or query == self.search_placeholder
        ):

            self.render_home()
            return

        self.current_view = "search"

        results = search_stations(
            query
        )

        stations = {}

        for category, category_stations in STATIONS.items():

            for name, url in category_stations.items():

                if name in results:

                    stations[name] = (
                        url,
                        category,
                    )

        self.section_title.config(
            text=f"Search  •  {query}"
        )

        self.clear_cards()

        self.render_station_grid(
            stations
        )

    # ========================================================
    # PLAY
    # ========================================================

    def play_station(
        self,
        name,
        url,
    ):

        self.current_station_name = name
        self.current_url = url

        category = self.get_station_category(
            name
        )

        self.station_title.config(
            text=name
        )

        self.station_category.config(
            text=category
        )

        self.station_status.config(
            text="● Connecting...",
            fg=self.WARNING,
        )

        self.track_label.config(
            text="♪  Connecting..."
        )

        self.player_station.config(
            text=name
        )

        self.player_track.config(
            text="Connecting..."
        )

        self.play_button.config(
            text="Ⅱ"
        )

        self.draw_cover(
            name,
            True,
        )

        self.update_favorite_button()

        self.set_live_state(
            "CONNECTING"
        )

        try:

            result = self.player.play(
                name,
                url,
            )

            if result is False:

                self.set_player_error(
                    "Unable to start stream"
                )

        except Exception as error:

            self.set_player_error(
                str(error)
            )

    # ========================================================
    # PLAY / PAUSE
    # ========================================================

    def toggle_play(self):

        if not self.current_station_name:
            return

        try:

            state = self.player.get_state()

            if state == "PLAYING":

                self.player.pause()

            elif state == "PAUSED":

                self.player.resume()

            elif state in (
                "STOPPED",
                "ERROR",
                "ENDED",
            ):

                self.player.play(
                    self.current_station_name,
                    self.current_url,
                )

            else:

                self.player.resume()

        except Exception as error:

            self.set_player_error(
                str(error)
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        try:
            self.player.stop()
        except Exception:
            pass

        self.set_live_state(
            "OFFLINE"
        )

        self.station_status.config(
            text="● Stopped",
            fg=self.TEXT_MUTED,
        )

        self.track_label.config(
            text="♪  No track information"
        )

        self.player_track.config(
            text="Playback stopped"
        )

        self.play_button.config(
            text="▶"
        )

        self.draw_cover(
            self.current_station_name or "RADIO",
            False,
        )

    # ========================================================
    # RANDOM
    # ========================================================

    def play_random(self):

        stations = []

        for category, category_stations in STATIONS.items():

            for name, url in category_stations.items():

                stations.append(
                    (name, url)
                )

        if not stations:
            return

        # Не выбираем ту же станцию,
        # если есть другие варианты.
        candidates = [
            station
            for station in stations
            if station[0] != self.current_station_name
        ]

        if candidates:
            stations = candidates

        name, url = random.choice(
            stations
        )

        self.play_station(
            name,
            url
        )

    # ========================================================
    # FAVORITES
    # ========================================================

    def toggle_station_favorite(
        self,
        name,
    ):

        if name in self.favorite_stations:

            self.favorite_stations.remove(
                name
            )

        else:

            self.favorite_stations.add(
                name
            )

        self.update_favorite_button()

        # Перерисовываем текущую страницу
        if self.current_view == "category":

            self.open_category(
                self.current_category
            )

        elif self.current_view == "favorites":

            self.show_favorites()

    def toggle_favorite(self):

        if not self.current_station_name:
            return

        self.toggle_station_favorite(
            self.current_station_name
        )

    def update_favorite_button(self):

        if (
            self.current_station_name
            in self.favorite_stations
        ):

            self.favorite_button.config(
                text="★",
                fg=self.ACCENT,
            )

        else:

            self.favorite_button.config(
                text="☆",
                fg=self.TEXT_MUTED,
            )

    def show_favorites(self):

        self.current_view = "favorites"
        self.current_category = None

        self.section_title.config(
            text="Favorites"
        )

        self.clear_cards()

        stations = {}

        for name in self.favorite_stations:

            for category, category_stations in STATIONS.items():

                if name in category_stations:

                    stations[name] = (
                        category_stations[name],
                        category,
                    )

        self.render_station_grid(
            stations
        )

    # ========================================================
    # HISTORY
    # ========================================================

    def add_to_history(
        self,
        name,
    ):

        if not name:
            return

        if name in self.history:

            self.history.remove(
                name
            )

        self.history.insert(
            0,
            name
        )

        self.history = self.history[:20]

    def show_history(self):

        self.current_view = "history"

        self.section_title.config(
            text="Recently played"
        )

        self.clear_cards()

        stations = {}

        for name in self.history:

            for category, category_stations in STATIONS.items():

                if name in category_stations:

                    stations[name] = (
                        category_stations[name],
                        category,
                    )

        self.render_station_grid(
            stations
        )

    # ========================================================
    # PLAYER CALLBACKS
    # ========================================================

    def _player_state_callback(
        self,
        state,
    ):

        # VLC callback может прийти из worker thread.
        # Передаём выполнение в Tkinter main thread.
        self.safe_after(
            lambda: self.handle_player_state(
                state
            )
        )

    def _player_error_callback(
        self,
        message,
    ):

        self.safe_after(
            lambda: self.set_player_error(
                message
            )
        )

    def _player_metadata_callback(
        self,
        title,
    ):

        self.safe_after(
            lambda: self.update_metadata(
                title
            )
        )

    # ========================================================
    # PLAYER STATE
    # ========================================================

    def handle_player_state(
        self,
        state,
    ):

        if self.closing:
            return

        self.last_state = state

        if state == "PLAYING":

            self.station_status.config(
                text="● Live now",
                fg=self.SUCCESS,
            )

            self.play_button.config(
                text="Ⅱ"
            )

            self.set_live_state(
                "LIVE"
            )

            self.add_to_history(
                self.current_station_name
            )

        elif state == "PAUSED":

            self.station_status.config(
                text="● Paused",
                fg=self.TEXT_MUTED,
            )

            self.play_button.config(
                text="▶"
            )

            self.set_live_state(
                "PAUSED"
            )

        elif state == "BUFFERING":

            self.station_status.config(
                text="● Buffering...",
                fg=self.WARNING,
            )

            self.set_live_state(
                "BUFFERING"
            )

        elif state == "CONNECTING":

            self.station_status.config(
                text="● Connecting...",
                fg=self.WARNING,
            )

            self.set_live_state(
                "CONNECTING"
            )

        elif state == "RECONNECTING":

            self.station_status.config(
                text="● Reconnecting...",
                fg=self.WARNING,
            )

            self.set_live_state(
                "RECONNECTING"
            )

        elif state == "STOPPED":

            self.station_status.config(
                text="● Stopped",
                fg=self.TEXT_MUTED,
            )

            self.play_button.config(
                text="▶"
            )

            self.set_live_state(
                "OFFLINE"
            )

        elif state == "ENDED":

            self.station_status.config(
                text="● Stream ended",
                fg=self.WARNING,
            )

            self.play_button.config(
                text="▶"
            )

            self.set_live_state(
                "OFFLINE"
            )

        elif state == "ERROR":

            self.set_player_error(
                "Stream connection error"
            )

    # ========================================================
    # METADATA
    # ========================================================

    def update_metadata(
        self,
        title,
    ):

        if not title:
            return

        title = str(title).strip()

        if not title:
            return

        if title == self.last_title:
            return

        self.last_title = title

        self.track_label.config(
            text=f"♪  {title}"
        )

        self.player_track.config(
            text=title
        )

    # ========================================================
    # UPDATE LOOP
    # ========================================================

    def update_loop(self):

        if self.closing:
            return

        try:

            state = self.player.get_state()

            # ------------------------------------------------
            # Metadata fallback
            # ------------------------------------------------

            if state in (
                "PLAYING",
                "BUFFERING",
                "CONNECTING",
            ):

                title = self.player.get_title()

                if title:
                    self.update_metadata(
                        title
                    )

            # ------------------------------------------------
            # Synchronize UI if callback missed
            # ------------------------------------------------

            if state != self.last_state:

                self.handle_player_state(
                    state
                )

        except Exception:
            pass

        if not self.closing:

            try:

                self.root.after(
                    max(
                        100,
                        int(UI_UPDATE_INTERVAL),
                    ),
                    self.update_loop,
                )

            except Exception:
                pass

    # ========================================================
    # LIVE STATUS
    # ========================================================

    def set_live_state(
        self,
        state,
    ):

        states = {

            "LIVE": (
                "●",
                "LIVE",
                self.SUCCESS,
            ),

            "CONNECTING": (
                "●",
                "CONNECTING",
                self.WARNING,
            ),

            "BUFFERING": (
                "●",
                "BUFFERING",
                self.WARNING,
            ),

            "RECONNECTING": (
                "●",
                "RECONNECTING",
                self.WARNING,
            ),

            "PAUSED": (
                "●",
                "PAUSED",
                self.TEXT_MUTED,
            ),

            "OFFLINE": (
                "●",
                "OFFLINE",
                self.TEXT_MUTED,
            ),

            "ERROR": (
                "●",
                "ERROR",
                self.ERROR,
            ),
        }

        dot, text, color = states.get(
            state,
            states["OFFLINE"],
        )

        self.live_dot.config(
            text=dot,
            fg=color,
        )

        self.live_text.config(
            text=text,
            fg=color,
        )

    # ========================================================
    # ERROR
    # ========================================================

    def set_player_error(
        self,
        message,
    ):

        if self.closing:
            return

        self.station_status.config(
            text="● Connection error",
            fg=self.ERROR,
        )

        self.track_label.config(
            text="♪  Unable to play this station"
        )

        self.player_track.config(
            text="Connection error"
        )

        self.play_button.config(
            text="▶"
        )

        self.set_live_state(
            "ERROR"
        )

    # ========================================================
    # VOLUME
    # ========================================================

    def initialize_volume(self):

        self.updating_volume = True

        try:

            self.volume_scale.set(
                DEFAULT_VOLUME
            )

        finally:

            self.updating_volume = False

        try:

            self.player.set_volume(
                DEFAULT_VOLUME
            )

        except Exception:
            pass

        self.update_volume_label(
            DEFAULT_VOLUME
        )

    def volume_changed(
        self,
        value,
    ):

        if self.updating_volume:
            return

        try:

            value = int(
                float(value)
            )

            value = max(
                0,
                min(
                    100,
                    value,
                ),
            )

            self.player.set_volume(
                value
            )

            self.update_volume_label(
                value
            )

        except Exception:
            pass

    def update_volume_label(
        self,
        value,
    ):

        value = int(value)

        self.volume_label.config(
            text=f"{value}%"
        )

    def change_volume(
        self,
        amount,
    ):

        try:

            current = self.player.get_volume()

            new_value = max(
                0,
                min(
                    100,
                    current + amount,
                ),
            )

            self.updating_volume = True

            try:

                self.volume_scale.set(
                    new_value
                )

            finally:

                self.updating_volume = False

            self.player.set_volume(
                new_value
            )

            self.update_volume_label(
                new_value
            )

        except Exception:
            pass

    # ========================================================
    # WAVEFORM
    # ========================================================

    def animate_waveform(self):

        if self.closing:
            return

        try:

            width = max(
                1,
                self.waveform.winfo_width()
            )

            height = max(
                1,
                self.waveform.winfo_height()
            )

            count = len(
                self.wave_bars
            )

            spacing = width / count

            active = self.last_state in (
                "PLAYING",
                "BUFFERING",
                "CONNECTING",
                "RECONNECTING",
            )

            for i, bar in enumerate(
                self.wave_bars
            ):

                if active:

                    wave = (
                        math.sin(
                            i * 0.55
                            + self.wave_phase
                        )
                        + 1
                    ) / 2

                    random_part = random.uniform(
                        0.45,
                        1.0
                    )

                    bar_height = (
                        6
                        + wave
                        * random_part
                        * 32
                    )

                else:

                    bar_height = 5

                x1 = (
                    i * spacing
                    + 1
                )

                x2 = (
                    (i + 1) * spacing
                    - 1
                )

                y2 = height

                y1 = max(
                    2,
                    height - bar_height,
                )

                self.waveform.coords(
                    bar,
                    x1,
                    y1,
                    x2,
                    y2,
                )

                self.waveform.itemconfig(
                    bar,
                    fill=(
                        self.ACCENT
                        if active
                        else self.SURFACE_3
                    ),
                )

            self.wave_phase += 0.17

        except Exception:
            pass

        if not self.closing:

            self.root.after(
                80,
                self.animate_waveform,
            )

    # ========================================================
    # SEARCH / VIEW HELPERS
    # ========================================================

    def get_station_category(
        self,
        station_name,
    ):

        for category, stations in STATIONS.items():

            if station_name in stations:
                return category

        return "Internet Radio"

    # ========================================================
    # SCROLL
    # ========================================================

    def on_scroll_content_configure(
        self,
        event=None,
    ):

        try:

            self.canvas.configure(
                scrollregion=self.canvas.bbox(
                    "all"
                )
            )

        except Exception:
            pass

    def on_canvas_configure(
        self,
        event=None,
    ):

        if not event:
            return

        try:

            self.canvas.itemconfigure(
                self.canvas_window,
                width=event.width,
            )

        except Exception:
            pass

    def on_mousewheel(
        self,
        event,
    ):

        try:

            self.canvas.yview_scroll(
                int(
                    -event.delta / 120
                ),
                "units",
            )

        except Exception:
            pass

    # ========================================================
    # HOTKEYS
    # ========================================================

    def setup_hotkeys(self):

        self.root.bind(
            "<space>",
            self._hotkey_play,
        )

        self.root.bind(
            "<Escape>",
            self._hotkey_stop,
        )

        self.root.bind(
            "<Up>",
            self._hotkey_volume_up,
        )

        self.root.bind(
            "<Down>",
            self._hotkey_volume_down,
        )

        self.root.bind(
            "<Control-k>",
            self._hotkey_search,
        )

        self.root.bind(
            "<Control-f>",
            self._hotkey_search,
        )

        self.root.bind(
            "f",
            self._hotkey_favorite,
        )

    def _hotkey_play(
        self,
        event=None,
    ):

        # Не перехватываем Space при вводе текста.
        if isinstance(
            self.root.focus_get(),
            tk.Entry,
        ):
            return

        self.toggle_play()

    def _hotkey_stop(
        self,
        event=None,
    ):

        self.stop()

    def _hotkey_volume_up(
        self,
        event=None,
    ):

        self.change_volume(
            5
        )

    def _hotkey_volume_down(
        self,
        event=None,
    ):

        self.change_volume(
            -5
        )

    def _hotkey_search(
        self,
        event=None,
    ):

        self.search_entry.focus_set()

        self.search_entry.select_range(
            0,
            "end",
        )

    def _hotkey_favorite(
        self,
        event=None,
    ):

        if isinstance(
            self.root.focus_get(),
            tk.Entry,
        ):
            return

        self.toggle_favorite()

    # ========================================================
    # SAFE TK CALLBACK
    # ========================================================

    def safe_after(
        self,
        callback,
    ):

        if self.closing:
            return

        try:

            self.root.after(
                0,
                callback,
            )

        except Exception:
            pass

    # ========================================================
    # CLOSE
    # ========================================================

    def on_closing(self):

        if self.closing:
            return

        self.closing = True

        # Cancel pending callbacks
        for after_id in self.ui_after_ids:

            try:
                self.root.after_cancel(
                    after_id
                )
            except Exception:
                pass

        # Player cleanup
        try:
            self.player.destroy()
        except Exception:
            pass

        # Tk cleanup
        try:
            self.root.destroy()
        except Exception:
            pass