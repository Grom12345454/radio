import sys
import os
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

from stations import STATIONS, search_stations, get_all_stations_flat, get_nested_structure
from player import RadioPlayer
from visualizer_3d import Visualizer3D
from ui.widgets_3d import Button3D, VolumeSlider3D, StationCard3D


class RadioApp3D:
    def __init__(self, root):
        self.root = root
        
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=BG)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # STATE
        self.current_station = None
        self.current_url = None
        self.selected_card = None
        self.station_cards = {}  # Храним ссылки на карточки
        
        self.closing = False
        self.updating_volume = False
        
        self.nested_structure = get_nested_structure()
        self.flat_stations = get_all_stations_flat()
        
        # PLAYER
        self.player = RadioPlayer()
        self.player.set_callbacks(
            on_state_changed=self.player_state_changed,
            on_error=self.player_error,
        )
        
        # UI
        self.setup_ui()
        self.setup_hotkeys()
        
        # INITIAL VOLUME
        self.updating_volume = True
        try:
            self.volume_scale.set(DEFAULT_VOLUME)
        finally:
            self.updating_volume = False
        
        self.player.set_volume(DEFAULT_VOLUME)
        self.update_volume_icon(DEFAULT_VOLUME)
        
        # VISUALIZER
        self.visualizer = Visualizer3D(
            self.visualizer_canvas,
            ACCENT,
            "#8b5cf6"
        )
        
        # UPDATE LOOP
        self.update_loop()
    
    def setup_ui(self):
        # HEADER
        header = tk.Frame(self.root, bg=BG, height=80)
        header.pack(fill="x", padx=30, pady=(20, 15))
        header.pack_propagate(False)
        
        logo_frame = tk.Frame(header, bg=BG)
        logo_frame.pack(side="left", padx=(0, 15))
        
        logo_canvas = tk.Canvas(logo_frame, width=50, height=50, bg=BG, highlightthickness=0)
        logo_canvas.pack()
        
        logo_canvas.create_oval(5, 5, 45, 45, fill=ACCENT, outline="")
        logo_canvas.create_text(25, 25, text="📻", fill="white", font=("Segoe UI Emoji", 24))
        
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        
        tk.Label(title_box, text=APP_NAME, bg=BG, fg=TEXT, font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(title_box, text="3D Internet Radio Player", bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w")
        
        # MAIN CONTENT
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=30, pady=5)
        
        # LEFT PANEL
        left_panel = tk.Frame(main, bg=PANEL, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="📡 РАДИОСТАНЦИИ", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=20, pady=(20, 15)
        )
        
        # Search
        search_frame = tk.Frame(left_panel, bg=PANEL_LIGHT)
        search_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.search_entry.pack(fill="x", padx=12, pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Station list with scroll
        list_container = tk.Frame(left_panel, bg=PANEL)
        list_container.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_container, bg=PANEL_LIGHT, troughcolor=PANEL, activebackground=ACCENT, relief="flat", borderwidth=0)
        scrollbar.pack(side="right", fill="y")
        
        self.stations_canvas = tk.Canvas(list_container, bg=PANEL, highlightthickness=0, yscrollcommand=scrollbar.set)
        self.stations_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=self.stations_canvas.yview)
        
        self.stations_frame = tk.Frame(self.stations_canvas, bg=PANEL)
        self.stations_canvas.create_window((0, 0), window=self.stations_frame, anchor="nw", width=340)
        
        self.stations_frame.bind("<Configure>", lambda e: self.stations_canvas.configure(scrollregion=self.stations_canvas.bbox("all")))
        
        self.populate_stations()
        
        # RIGHT PANEL
        right_panel = tk.Frame(main, bg=BG)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # Station card
        station_card = tk.Frame(right_panel, bg=PANEL)
        station_card.pack(fill="x", pady=(0, 15))
        
        cover_frame = tk.Frame(station_card, bg=PANEL)
        cover_frame.pack(side="left", padx=25, pady=25)
        
        self.cover_canvas = tk.Canvas(cover_frame, width=150, height=150, bg=PANEL_LIGHT, highlightthickness=0)
        self.cover_canvas.pack()
        self.draw_3d_cover()
        
        info_frame = tk.Frame(station_card, bg=PANEL)
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 25))
        
        self.station_title = tk.Label(info_frame, text="Выберите станцию", bg=PANEL, fg=TEXT, font=("Segoe UI", 20, "bold"), wraplength=500, justify="left")
        self.station_title.pack(anchor="w", pady=(35, 8))
        
        self.status_label = tk.Label(info_frame, text="● Готов к воспроизведению", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 11))
        self.status_label.pack(anchor="w")
        
        self.track_label = tk.Label(info_frame, text="", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 10))
        self.track_label.pack(anchor="w", pady=(15, 0))
        
        # Visualizer
        visualizer_frame = tk.Frame(right_panel, bg=PANEL)
        visualizer_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(visualizer_frame, text="🎵 AUDIO VISUALIZER", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.visualizer_canvas = tk.Canvas(visualizer_frame, bg=PANEL, highlightthickness=0)
        self.visualizer_canvas.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Controls
        controls_frame = tk.Frame(right_panel, bg=PANEL_LIGHT)
        controls_frame.pack(fill="x")
        
        buttons_frame = tk.Frame(controls_frame, bg=PANEL_LIGHT)
        buttons_frame.pack(side="left", padx=20, pady=15)
        
        self.play_button = Button3D(buttons_frame, text="▶  PLAY", command=self.toggle_play, bg=ACCENT)
        self.play_button.pack(side="left", padx=5)
        
        self.stop_button = Button3D(buttons_frame, text="■  STOP", command=self.stop, bg=PANEL_HOVER)
        self.stop_button.pack(side="left", padx=5)
        
        volume_frame = tk.Frame(controls_frame, bg=PANEL_LIGHT)
        volume_frame.pack(side="right", padx=20)
        
        self.volume_icon = tk.Label(volume_frame, text="🔊", bg=PANEL_LIGHT, fg=TEXT, font=("Segoe UI Emoji", 14))
        self.volume_icon.pack(side="left", padx=(0, 8))
        
        self.volume_scale = VolumeSlider3D(volume_frame, command=self.volume_changed)
        self.volume_scale.pack(side="left")
        
        # FOOTER
        footer = tk.Frame(self.root, bg=PANEL_LIGHT, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        self.footer_status = tk.Label(footer, text="● OFFLINE", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.footer_status.pack(side="left", padx=20, pady=6)
        
        tk.Label(footer, text=f"{APP_NAME} v{APP_VERSION}", bg=PANEL_LIGHT, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="right", padx=20)
    
    def draw_3d_cover(self):
        canvas = self.cover_canvas
        canvas.delete("all")
        
        for i in range(5, 0, -1):
            offset = i * 2
            canvas.create_rectangle(offset, offset, 150 - offset, 150 - offset, fill="#1f2937", outline="")
        
        canvas.create_rectangle(10, 10, 140, 140, fill=ACCENT, outline="")
        
        for i in range(10):
            canvas.create_rectangle(10, 10 + i * 13, 140, 140, fill="#8b5cf6", outline="", stipple="gray50")
        
        canvas.create_text(75, 75, text="♪", fill="white", font=("Segoe UI", 60, "bold"))
    
    def setup_hotkeys(self):
        self.root.bind("<space>", lambda event: self.toggle_play())
        self.root.bind("<Escape>", lambda event: self.stop())
        self.root.bind("<Up>", lambda event: self.change_volume(5))
        self.root.bind("<Down>", lambda event: self.change_volume(-5))
    
    def populate_stations(self):
        """Заполняет список станций в виде карточек"""
        for widget in self.stations_frame.winfo_children():
            widget.destroy()
        
        self.station_cards = {}
        
        for category, content in self.nested_structure.items():
            # Заголовок категории
            cat_header = tk.Frame(self.stations_frame, bg=PANEL)
            cat_header.pack(fill="x", padx=15, pady=(15, 8))
            
            tk.Label(cat_header, text=category, bg=PANEL, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
            
            # Добавляем станции
            self._add_stations_as_cards(content, self.stations_frame, level=1)
    
    def _add_stations_as_cards(self, content, parent, level=0):
        """Добавляет станции в виде карточек"""
        indent = level * 10
        
        for name, value in content.items():
            if isinstance(value, str):
                # Это станция
                card = StationCard3D(
                    parent,
                    station_name=name,
                    station_url=value,
                    genre="",
                    on_click_callback=self.select_station
                )
                card.pack(fill="x", padx=(15 + indent, 15), pady=3)
                
                # Сохраняем ссылку на карточку
                self.station_cards[name] = card
                
            elif isinstance(value, dict):
                has_only_urls = all(isinstance(v, str) for v in value.values())
                
                if has_only_urls and level == 0:
                    for sub_name, sub_url in value.items():
                        card = StationCard3D(
                            parent,
                            station_name=sub_name,
                            station_url=sub_url,
                            genre=name,
                            on_click_callback=self.select_station
                        )
                        card.pack(fill="x", padx=(15 + indent, 15), pady=3)
                        self.station_cards[sub_name] = card
                else:
                    subcat_header = tk.Frame(parent, bg=PANEL)
                    subcat_header.pack(fill="x", padx=(15 + indent, 15), pady=(8, 2))
                    
                    tk.Label(subcat_header, text=f"  └ {name}", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w")
                    
                    self._add_stations_as_cards(value, parent, level=level + 1)
    
    def select_station(self, card):
        """Выбирает станцию для воспроизведения"""
        if self.selected_card:
            self.selected_card.deselect()
        
        card.select()
        self.selected_card = card
        
        station_name = card.station_name
        url = card.station_url
        
        if not url:
            self.player_error("URL станции не найден")
            return
        
        self.current_station = station_name
        self.current_url = url
        
        self.station_title.config(text=station_name)
        self.track_label.config(text="")
        
        self.set_status("● Подключение...", WARNING)
        self.footer_status.config(text="● CONNECTING", fg=WARNING)
        self.play_button.config(text="⏸  PAUSE")
        
        try:
            self.player.play(station_name, url)
        except Exception as exc:
            self.player_error(str(exc))
    
    def on_search(self, event=None):
        query = self.search_var.get()
        
        if not query:
            self.populate_stations()
        else:
            # Фильтруем и показываем только найденные
            filtered = search_stations(query)
            self._show_filtered_stations(filtered)
    
    def _show_filtered_stations(self, filtered_stations):
        """Показывает отфильтрованные станции"""
        for widget in self.stations_frame.winfo_children():
            widget.destroy()
        
        for name, url in filtered_stations.items():
            card = StationCard3D(
                self.stations_frame,
                station_name=name,
                station_url=url,
                on_click_callback=self.select_station
            )
            card.pack(fill="x", padx=15, pady=3)
            self.station_cards[name] = card
    
    def toggle_play(self):
        if not self.current_station:
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
        
        self.play_button.config(text="▶  PLAY")
        self.set_status("● Остановлено", TEXT_MUTED)
        self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
        self.track_label.config(text="")
    
    def player_state_changed(self, state):
        if self.closing:
            return
        
        try:
            if state == "CONNECTING":
                self.set_status("● Подключение...", WARNING)
                self.footer_status.config(text="● CONNECTING", fg=WARNING)
                self.play_button.config(text="⏸  PAUSE")
            
            elif state == "PLAYING":
                self.set_status("● Сейчас играет", SUCCESS)
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
                self.play_button.config(text="⏸  PAUSE")
            
            elif state == "PAUSED":
                self.set_status("● Пауза", TEXT_MUTED)
                self.footer_status.config(text="● PAUSED", fg=TEXT_MUTED)
                self.play_button.config(text="▶  RESUME")
            
            elif state == "STOPPED":
                self.set_status("● Остановлено", TEXT_MUTED)
                self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
                self.play_button.config(text="▶  PLAY")
            
            elif state == "ERROR":
                self.set_status("● Ошибка", ERROR)
                self.footer_status.config(text="● ERROR", fg=ERROR)
                self.play_button.config(text="▶  PLAY")
            
            elif state == "ENDED":
                self.set_status("● Поток завершён", TEXT_MUTED)
                self.footer_status.config(text="● OFFLINE", fg=TEXT_MUTED)
                self.play_button.config(text="▶  PLAY")
        
        except tk.TclError:
            pass
    
    def player_error(self, text):
        if self.closing:
            return
        
        self.set_status("● Ошибка подключения", ERROR)
        
        try:
            self.footer_status.config(text="● ERROR", fg=ERROR)
            self.play_button.config(text="▶  PLAY")
        except tk.TclError:
            pass
    
    def set_status(self, text, color):
        try:
            self.status_label.config(text=text, fg=color)
        except tk.TclError:
            pass
    
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
                self.volume_icon.config(text="🔈")
            elif value < 75:
                self.volume_icon.config(text="🔉")
            else:
                self.volume_icon.config(text="🔊")
        
        except (ValueError, TypeError, tk.TclError):
            pass
    
    def update_loop(self):
        if self.closing:
            return
        
        try:
            state = self.player.get_state()
            
            if state == "PLAYING":
                self.footer_status.config(text="● LIVE", fg=SUCCESS)
                
                # Обновляем метаданные
                title = self.player.get_title()
                if title:
                    self.track_label.config(text=f"♪ {title}")
                    
                    # Обновляем информацию в карточке
                    if self.selected_card and hasattr(self.selected_card, 'update_now_playing'):
                        self.selected_card.update_now_playing(title)
            
            # Визуализатор
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