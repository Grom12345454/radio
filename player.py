import threading
import time
from urllib.parse import urlparse

import vlc

from config import (
    NETWORK_CACHING,
    AUTO_RECONNECT,
    MAX_RECONNECT_ATTEMPTS,
)

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class RadioPlayer:
    """
    VLC-плеер для радио.

    Поддерживает:
        - MP3
        - AAC / AAC+
        - HTTP / HTTPS radio streams
        - HLS (.m3u8)
        - YouTube / YouTube Live через yt-dlp

    Callback API:
        on_state_changed
        on_metadata_changed
        on_error
    """

    HLS_NETWORK_CACHING = max(
        int(NETWORK_CACHING),
        3000,
    )

    YOUTUBE_EXTRACT_TIMEOUT = 30
    RECONNECT_DELAY = 3

    def __init__(self):
        self.instance = vlc.Instance(
            "--no-video",
            "--quiet",
        )

        self.player = self.instance.media_player_new()

        self.current_station = None
        self.current_url = None
        self.current_play_url = None
        self.source_type = None

        self.volume = 75

        self.reconnect_attempts = 0
        self._reconnect_thread = None
        self._reconnect_lock = threading.Lock()

        self._manual_stop = False

        # ----------------------------------------------------
        # Callbacks
        # ----------------------------------------------------

        self.on_state_changed = None
        self.on_metadata_changed = None
        self.on_error = None

        # ----------------------------------------------------
        # VLC events
        # ----------------------------------------------------

        self.event_manager = self.player.event_manager()

        self.event_manager.event_attach(
            vlc.EventType.MediaPlayerPlaying,
            self._on_vlc_playing,
        )

        self.event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_vlc_end,
        )

        self.event_manager.event_attach(
            vlc.EventType.MediaPlayerEncounteredError,
            self._on_vlc_error,
        )

        self.event_manager.event_attach(
            vlc.EventType.MediaMetaChanged,
            self._on_vlc_metadata,
        )

    # ========================================================
    # CALLBACKS
    # ========================================================

    def set_callbacks(
        self,
        on_state_changed=None,
        on_metadata_changed=None,
        on_error=None,
        **kwargs,
    ):
        self.on_state_changed = on_state_changed
        self.on_metadata_changed = on_metadata_changed
        self.on_error = on_error

    def notify_state(self, state):
        if self.on_state_changed is not None:
            try:
                self.on_state_changed(state)
            except Exception:
                pass

    def notify_metadata(self, metadata):
        if self.on_metadata_changed is not None:
            try:
                self.on_metadata_changed(metadata)
            except Exception:
                pass

    def notify_error(self, message):
        if self.on_error is not None:
            try:
                self.on_error(message)
            except Exception:
                pass

    # ========================================================
    # URL HELPERS
    # ========================================================

    @staticmethod
    def _normalize_url(url):
        if url is None:
            return ""

        return str(url).strip()

    @classmethod
    def _is_youtube_url(cls, url):
        url = cls._normalize_url(url)

        if not url:
            return False

        try:
            parsed = urlparse(url)

            host = (
                parsed.netloc or ""
            ).lower().split(":")[0]

            return host in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "music.youtube.com",
                "youtu.be",
                "www.youtu.be",
            }

        except Exception:
            return False

    @classmethod
    def _is_hls_url(cls, url):
        url = cls._normalize_url(url).lower()

        if not url:
            return False

        if ".m3u8" in url:
            return True

        if "format=m3u8" in url:
            return True

        if "manifest" in url and (
            "m3u" in url
            or "hls" in url
        ):
            return True

        return False

    # --------------------------------------------------------
    # Публичные методы.
    #
    # Они нужны ui/app.py.
    # --------------------------------------------------------

    def is_youtube_url(self, url):
        """
        Проверяет, является ли URL YouTube.

        Этот метод специально публичный,
        потому что ui/app.py вызывает:
            self.player.is_youtube_url(url)
        """

        return self._is_youtube_url(url)

    def is_hls_url(self, url):
        """
        Проверяет, является ли URL HLS.
        """

        return self._is_hls_url(url)

    def get_source_type_for_url(self, url):
        """
        Возвращает тип URL:
            youtube
            hls
            radio
        """

        if self.is_youtube_url(url):
            return "youtube"

        if self.is_hls_url(url):
            return "hls"

        return "radio"

    @classmethod
    def _get_source_type(cls, url):
        if cls._is_youtube_url(url):
            return "youtube"

        if cls._is_hls_url(url):
            return "hls"

        return "radio"

    # ========================================================
    # YOUTUBE
    # ========================================================

    def _extract_youtube_stream(self, url):
        if yt_dlp is None:
            raise RuntimeError(
                "Для YouTube требуется yt-dlp. "
                "Установите его командой: "
                "python -m pip install -U yt-dlp"
            )

        options = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "cachedir": False,
            "socket_timeout": self.YOUTUBE_EXTRACT_TIMEOUT,

            "format": (
                "best[protocol*=m3u8]/"
                "bestaudio/best"
            ),
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                url,
                download=False,
            )

        if not info:
            raise RuntimeError(
                "yt-dlp не получил данные YouTube."
            )

        direct_url = info.get("url")

        if not direct_url:
            direct_url = info.get(
                "manifest_url"
            )

        if not direct_url:
            formats = info.get("formats") or []

            candidates = []

            for fmt in formats:
                fmt_url = fmt.get("url")

                if not fmt_url:
                    continue

                acodec = fmt.get("acodec")

                if acodec in (
                    None,
                    "none",
                ):
                    continue

                protocol = str(
                    fmt.get("protocol") or ""
                ).lower()

                score = 0

                if "m3u8" in protocol:
                    score += 1000

                if fmt.get("abr"):
                    score += int(
                        fmt.get("abr") or 0
                    )

                if fmt.get("tbr"):
                    score += int(
                        fmt.get("tbr") or 0
                    )

                candidates.append(
                    (
                        score,
                        fmt_url,
                    )
                )

            if candidates:
                candidates.sort(
                    key=lambda item: item[0],
                    reverse=True,
                )

                direct_url = candidates[0][1]

        if not direct_url:
            raise RuntimeError(
                "Не удалось получить прямой "
                "URL YouTube-потока."
            )

        if self.is_hls_url(direct_url):
            stream_type = "hls"
        else:
            stream_type = "radio"

        return direct_url, stream_type

    # ========================================================
    # VLC MEDIA
    # ========================================================

    def _create_media(
        self,
        url,
        source_type,
    ):
        media = self.instance.media_new(url)

        if source_type == "hls":
            media.add_option(
                ":network-caching={}".format(
                    self.HLS_NETWORK_CACHING
                )
            )

            media.add_option(
                ":http-reconnect=true"
            )

            media.add_option(
                ":http-continuous=true"
            )

        else:
            media.add_option(
                ":network-caching={}".format(
                    NETWORK_CACHING
                )
            )

            media.add_option(
                ":http-reconnect=true"
            )

        return media

    # ========================================================
    # DIRECT PLAY
    # ========================================================

    def _play_direct(
        self,
        direct_url,
        source_type,
    ):
        media = self._create_media(
            direct_url,
            source_type,
        )

        self.current_play_url = direct_url
        self.source_type = source_type

        self.player.set_media(media)

        result = self.player.play()

        if result == -1:
            raise RuntimeError(
                "VLC не смог запустить поток."
            )

        self.set_volume(self.volume)

        self.notify_state(
            "CONNECTING"
        )

        return True

    # ========================================================
    # PLAY
    # ========================================================

    def play(
        self,
        station_name,
        url,
    ):
        url = self._normalize_url(url)

        if not url:
            self.notify_state("ERROR")

            self.notify_error(
                "URL потока пустой."
            )

            return False

        self._manual_stop = True

        try:
            self.player.stop()
        except Exception:
            pass

        self._manual_stop = False

        self.current_station = station_name
        self.current_url = url
        self.current_play_url = None

        self.reconnect_attempts = 0

        source_type = self.get_source_type_for_url(
            url
        )

        self.source_type = source_type

        try:
            # ------------------------------------------------
            # YouTube
            # ------------------------------------------------

            if source_type == "youtube":
                self.notify_state(
                    "CONNECTING"
                )

                (
                    direct_url,
                    extracted_type,
                ) = self._extract_youtube_stream(
                    url
                )

                return self._play_direct(
                    direct_url,
                    extracted_type,
                )

            # ------------------------------------------------
            # HLS / обычное радио
            # ------------------------------------------------

            return self._play_direct(
                url,
                source_type,
            )

        except Exception as error:
            self.notify_state("ERROR")

            self.notify_error(
                "Ошибка запуска: {}".format(
                    error
                )
            )

            if AUTO_RECONNECT:
                self._schedule_reconnect()

            return False

    # ========================================================
    # RECONNECT
    # ========================================================

    def _schedule_reconnect(self):
        if not AUTO_RECONNECT:
            return

        if not self.current_url:
            return

        with self._reconnect_lock:
            if (
                self._reconnect_thread
                and self._reconnect_thread.is_alive()
            ):
                return

            self._reconnect_thread = (
                threading.Thread(
                    target=self._reconnect_worker,
                    daemon=True,
                )
            )

            self._reconnect_thread.start()

    def _reconnect_worker(self):
        while True:
            if self._manual_stop:
                return

            if not self.current_url:
                return

            if self.player.is_playing():
                return

            if (
                self.reconnect_attempts
                >= MAX_RECONNECT_ATTEMPTS
            ):
                self.notify_state(
                    "ERROR"
                )

                self.notify_error(
                    "Не удалось восстановить "
                    "поток после {} попыток.".format(
                        MAX_RECONNECT_ATTEMPTS
                    )
                )

                return

            self.reconnect_attempts += 1

            self.notify_state(
                "RECONNECTING"
            )

            time.sleep(
                self.RECONNECT_DELAY
            )

            if self._manual_stop:
                return

            try:
                url = self.current_url

                source_type = (
                    self.get_source_type_for_url(
                        url
                    )
                )

                # Для YouTube временный URL
                # необходимо получить заново.
                if source_type == "youtube":
                    (
                        direct_url,
                        extracted_type,
                    ) = self._extract_youtube_stream(
                        url
                    )

                    self._play_direct(
                        direct_url,
                        extracted_type,
                    )

                else:
                    self._play_direct(
                        url,
                        source_type,
                    )

                # Ждём запуска VLC.
                for _ in range(20):
                    if self._manual_stop:
                        return

                    if self.player.is_playing():
                        self.notify_state(
                            "PLAYING"
                        )

                        return

                    time.sleep(0.25)

            except Exception:
                continue

    # ========================================================
    # PAUSE
    # ========================================================

    def pause(self):
        try:
            if self.player.is_playing():
                self.player.pause()

                self.notify_state(
                    "PAUSED"
                )

                return True

        except Exception:
            pass

        return False

    # ========================================================
    # RESUME
    # ========================================================

    def resume(self):
        try:
            self.player.play()

            self.notify_state(
                "PLAYING"
            )

            return True

        except Exception:
            return False

    # ========================================================
    # TOGGLE
    # ========================================================

    def toggle_pause(self):
        try:
            if self.player.is_playing():
                return self.pause()

            return self.resume()

        except Exception:
            return False

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):
        self._manual_stop = True

        try:
            self.player.stop()
        except Exception:
            pass

        self.current_play_url = None
        self.source_type = None
        self.reconnect_attempts = 0

        self.notify_state(
            "STOPPED"
        )

    # ========================================================
    # VOLUME
    # ========================================================

    def set_volume(self, value):
        try:
            value = float(value)

            value = max(
                0,
                min(100, value),
            )

            self.volume = int(value)

            self.player.audio_set_volume(
                self.volume
            )

            return self.volume

        except Exception:
            return self.volume

    def get_volume(self):
        return self.volume

    # ========================================================
    # STATE
    # ========================================================

    def is_playing(self):
        try:
            return self.player.is_playing()

        except Exception:
            return False

    def get_state(self):
        try:
            state = self.player.get_state()

            if state == vlc.State.Playing:
                return "PLAYING"

            if state == vlc.State.Paused:
                return "PAUSED"

            if state == vlc.State.Buffering:
                return "BUFFERING"

            if state == vlc.State.Error:
                return "ERROR"

            if state == vlc.State.Ended:
                return "ENDED"

            if state == vlc.State.Stopped:
                return "STOPPED"

            return "CONNECTING"

        except Exception:
            return "ERROR"

    # ========================================================
    # SOURCE
    # ========================================================

    def get_source_type(self):
        return self.source_type

    def get_current_url(self):
        return self.current_url

    def get_current_play_url(self):
        return self.current_play_url

    # ========================================================
    # METADATA
    # ========================================================

    def get_title(self):
        try:
            media = self.player.get_media()

            if media is None:
                return None

            title = media.get_meta(
                vlc.Meta.NowPlaying
            )

            if title:
                return title

            title = media.get_meta(
                vlc.Meta.Title
            )

            if title:
                return title

            return None

        except Exception:
            return None

    def _get_metadata(self):
        try:
            media = self.player.get_media()

            if media is None:
                return {}

            metadata = {}

            meta_map = {
                "title": vlc.Meta.Title,
                "now_playing": vlc.Meta.NowPlaying,
                "artist": vlc.Meta.Artist,
                "album": vlc.Meta.Album,
                "genre": vlc.Meta.Genre,
                "description": vlc.Meta.Description,
                "url": vlc.Meta.URL,
            }

            for key, meta_type in meta_map.items():
                try:
                    value = media.get_meta(
                        meta_type
                    )

                    if value:
                        metadata[key] = value

                except Exception:
                    pass

            return metadata

        except Exception:
            return {}

    def _on_vlc_metadata(self, event=None):
        try:
            metadata = self._get_metadata()

            if metadata:
                self.notify_metadata(
                    metadata
                )

        except Exception:
            pass

    # ========================================================
    # VLC EVENTS
    # ========================================================

    def _on_vlc_playing(self, event=None):
        self.reconnect_attempts = 0

        self.notify_state(
            "PLAYING"
        )

        self._on_vlc_metadata()

    def _on_vlc_end(self, event=None):
        if self._manual_stop:
            return

        self.notify_state(
            "ENDED"
        )

        if AUTO_RECONNECT:
            self._schedule_reconnect()

    def _on_vlc_error(self, event=None):
        if self._manual_stop:
            return

        self.notify_state(
            "ERROR"
        )

        if AUTO_RECONNECT:
            self._schedule_reconnect()

    # ========================================================
    # DESTROY
    # ========================================================

    def destroy(self):
        self._manual_stop = True

        try:
            self.player.stop()
        except Exception:
            pass

        try:
            self.player.release()
        except Exception:
            pass

        try:
            self.instance.release()
        except Exception:
            pass

        self.current_station = None
        self.current_url = None
        self.current_play_url = None
        self.source_type = None
