import threading
import time
from typing import Callable, Optional

import vlc

from config import (
    NETWORK_CACHING,
    AUTO_RECONNECT,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_DELAY,
    DEFAULT_VOLUME,
)


class RadioPlayer:
    """
    Надёжный VLC-плеер для интернет-радио.

    Совместим с существующим UI проекта:
        play(station_name, url)
        pause()
        resume()
        toggle_pause()
        stop()
        set_volume(value)
        get_volume()
        is_playing()
        get_state()
        get_title()
        destroy()

    Дополнительно:
        mute()
        toggle_mute()
        is_muted()
        get_current_station()
        get_current_url()
    """

    def __init__(self):
        # --------------------------------------------------
        # VLC
        # --------------------------------------------------

        self.instance = vlc.Instance(
            "--no-video",
            "--quiet",
            "--intf",
            "dummy",
        )

        self.player = self.instance.media_player_new()

        # --------------------------------------------------
        # Состояние
        # --------------------------------------------------

        self.current_url: Optional[str] = None
        self.current_station: Optional[str] = None

        self.volume = max(0, min(100, int(DEFAULT_VOLUME)))
        self._previous_volume = self.volume

        self._muted = False
        self._destroyed = False

        self.reconnect_attempts = 0

        # Защита от нескольких потоков одновременно
        self._lock = threading.RLock()

        # Поток автоматического мониторинга
        self._monitor_thread = None
        self._monitor_stop = threading.Event()

        # События
        self.on_state_changed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_metadata_changed: Optional[Callable] = None

        self._last_state = None
        self._last_title = None

        # --------------------------------------------------
        # Запускаем мониторинг
        # --------------------------------------------------

        self._start_monitor()

    # ======================================================
    # CALLBACKS
    # ======================================================

    def set_callbacks(
        self,
        on_state_changed=None,
        on_error=None,
        on_metadata_changed=None,
    ):
        """
        Подключение callback-функций.

        on_state_changed(state)
        on_error(message)
        on_metadata_changed(title)
        """

        self.on_state_changed = on_state_changed
        self.on_error = on_error
        self.on_metadata_changed = on_metadata_changed

    def notify_state(self, state):
        """Безопасно отправляет изменение состояния."""

        if state == self._last_state:
            return

        self._last_state = state

        callback = self.on_state_changed

        if callback:
            try:
                callback(state)
            except Exception:
                pass

    def notify_error(self, message):
        """Безопасно отправляет ошибку."""

        callback = self.on_error

        if callback:
            try:
                callback(message)
            except Exception:
                pass

    def notify_metadata(self, title):
        """Сообщает UI об изменении текущего трека."""

        if title == self._last_title:
            return

        self._last_title = title

        callback = self.on_metadata_changed

        if callback:
            try:
                callback(title)
            except Exception:
                pass

    # ======================================================
    # PLAY
    # ======================================================

    def play(self, station_name, url):
        """
        Запускает радиостанцию.

        Возвращает:
            True  - VLC принял поток
            False - произошла ошибка
        """

        if self._destroyed:
            return False

        if not url:
            self.notify_state("ERROR")
            self.notify_error("У радиостанции отсутствует URL.")
            return False

        with self._lock:
            try:
                # Останавливаем предыдущий поток
                self._stop_internal(notify=False)

                self.current_station = station_name
                self.current_url = url

                self.reconnect_attempts = 0
                self._last_title = None

                self.notify_state("CONNECTING")

                # --------------------------------------------------
                # Создаём media
                # --------------------------------------------------

                media = self.instance.media_new(url)

                # Буфер
                media.add_option(
                    f":network-caching={int(NETWORK_CACHING)}"
                )

                # Автоматический HTTP reconnect
                media.add_option(":http-reconnect=true")

                # TCP reconnect
                media.add_option(":network-timeout=10000")

                # Не пытаться открыть видео
                media.add_option(":no-video")

                # --------------------------------------------------
                # Устанавливаем media
                # --------------------------------------------------

                self.player.set_media(media)

                # Громкость
                self.player.audio_set_volume(self.volume)

                result = self.player.play()

                if result == -1:
                    self.notify_state("ERROR")
                    self.notify_error(
                        f"Не удалось запустить поток: {station_name}"
                    )
                    return False

                return True

            except Exception as error:
                self.notify_state("ERROR")
                self.notify_error(
                    f"Ошибка запуска радиостанции: {error}"
                )
                return False

    # ======================================================
    # PAUSE / RESUME
    # ======================================================

    def pause(self):
        """Поставить воспроизведение на паузу."""

        if self._destroyed:
            return False

        try:
            if self.player.is_playing():
                self.player.pause()
                self.notify_state("PAUSED")
                return True

            return False

        except Exception as error:
            self.notify_error(f"Ошибка паузы: {error}")
            return False

    def resume(self):
        """Продолжить воспроизведение."""

        if self._destroyed:
            return False

        try:
            result = self.player.play()

            if result == -1:
                self.notify_state("ERROR")
                return False

            self.notify_state("PLAYING")
            return True

        except Exception as error:
            self.notify_error(f"Ошибка продолжения: {error}")
            return False

    def toggle_pause(self):
        """Переключить Play/Pause."""

        if self._destroyed:
            return False

        try:
            state = self.get_state()

            if state == "PAUSED":
                return self.resume()

            if state in ("PLAYING", "BUFFERING", "CONNECTING"):
                return self.pause()

            if self.current_url:
                return self.play(
                    self.current_station or "Radio",
                    self.current_url,
                )

            return False

        except Exception:
            return False

    # ======================================================
    # STOP
    # ======================================================

    def _stop_internal(self, notify=True):
        try:
            self.player.stop()
        except Exception:
            pass

        if notify:
            self.notify_state("STOPPED")

    def stop(self):
        """Полностью остановить текущую станцию."""

        with self._lock:
            self._stop_internal(notify=True)

            self.reconnect_attempts = 0
            self._last_title = None

    # ======================================================
    # VOLUME
    # ======================================================

    def set_volume(self, value):
        """Установить громкость 0-100."""

        try:
            value = int(float(value))
        except (TypeError, ValueError):
            return self.volume

        value = max(0, min(100, value))

        self.volume = value

        # Если громкость подняли вручную,
        # снимаем mute.
        if value > 0:
            self._muted = False

        try:
            self.player.audio_set_volume(value)
        except Exception:
            pass

        return self.volume

    def get_volume(self):
        return self.volume

    # ======================================================
    # MUTE
    # ======================================================

    def mute(self):
        """Выключить звук."""

        if self._muted:
            return

        self._previous_volume = self.volume
        self._muted = True

        try:
            self.player.audio_set_volume(0)
        except Exception:
            pass

    def unmute(self):
        """Вернуть звук."""

        if not self._muted:
            return

        self._muted = False

        volume = self._previous_volume

        if volume <= 0:
            volume = DEFAULT_VOLUME

        self.volume = int(volume)

        try:
            self.player.audio_set_volume(self.volume)
        except Exception:
            pass

    def toggle_mute(self):
        """Переключить mute."""

        if self._muted:
            self.unmute()
        else:
            self.mute()

        return self._muted

    def is_muted(self):
        return self._muted

    # ======================================================
    # STATUS
    # ======================================================

    def is_playing(self):
        try:
            return bool(self.player.is_playing())
        except Exception:
            return False

    def get_state(self):
        """Возвращает состояние VLC в виде строки."""

        if self._destroyed:
            return "STOPPED"

        try:
            state = self.player.get_state()

            mapping = {
                vlc.State.Playing: "PLAYING",
                vlc.State.Paused: "PAUSED",
                vlc.State.Buffering: "BUFFERING",
                vlc.State.Error: "ERROR",
                vlc.State.Ended: "ENDED",
                vlc.State.Stopped: "STOPPED",
                vlc.State.Opening: "CONNECTING",
                vlc.State.NothingSpecial: "CONNECTING",
            }

            return mapping.get(state, "CONNECTING")

        except Exception:
            return "ERROR"

    # ======================================================
    # CURRENT STATION
    # ======================================================

    def get_current_station(self):
        return self.current_station

    def get_current_url(self):
        return self.current_url

    # ======================================================
    # METADATA
    # ======================================================

    def get_title(self):
        """
        Получает Now Playing / Title из VLC.

        Возвращает None, если metadata пока отсутствует.
        """

        try:
            media = self.player.get_media()

            if media is None:
                return None

            # Иногда VLC отдаёт NowPlaying
            title = media.get_meta(vlc.Meta.NowPlaying)

            if title:
                return str(title).strip()

            # Иногда только Title
            title = media.get_meta(vlc.Meta.Title)

            if title:
                return str(title).strip()

            return None

        except Exception:
            return None

    # ======================================================
    # MONITOR
    # ======================================================

    def _start_monitor(self):
        """Запускает фоновый монитор VLC."""

        self._monitor_stop.clear()

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="RadioPlayerMonitor",
        )

        self._monitor_thread.start()

    def _monitor_loop(self):
        """
        Фоновый мониторинг:

        - состояния VLC;
        - metadata;
        - обрывов;
        - reconnect.
        """

        last_check = time.monotonic()

        while not self._monitor_stop.is_set():

            try:
                state = self.get_state()

                # --------------------------------------------------
                # Состояние
                # --------------------------------------------------

                if state != self._last_state:
                    self.notify_state(state)

                # --------------------------------------------------
                # Metadata
                # --------------------------------------------------

                if state in (
                    "PLAYING",
                    "BUFFERING",
                    "CONNECTING",
                ):
                    title = self.get_title()

                    if title:
                        self.notify_metadata(title)

                # --------------------------------------------------
                # Reconnect
                # --------------------------------------------------

                if (
                    AUTO_RECONNECT
                    and self.current_url
                    and state in ("ERROR", "ENDED")
                ):
                    now = time.monotonic()

                    # Не пытаемся переподключаться слишком часто
                    if now - last_check >= RECONNECT_DELAY / 1000:
                        last_check = now
                        self._try_reconnect()

                # --------------------------------------------------
                # Небольшая пауза
                # --------------------------------------------------

                self._monitor_stop.wait(0.5)

            except Exception:
                self._monitor_stop.wait(1.0)

    def _try_reconnect(self):
        """Попытка переподключения."""

        if self._destroyed:
            return

        if not self.current_url:
            return

        if self.reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
            self.notify_state("ERROR")
            self.notify_error(
                "Не удалось подключиться к радиостанции."
            )
            return

        self.reconnect_attempts += 1

        attempt = self.reconnect_attempts

        self.notify_state("RECONNECTING")

        # --------------------------------------------------
        # Небольшая задержка.
        # Каждый следующий retry немного дольше.
        # --------------------------------------------------

        delay = max(
            0.5,
            (RECONNECT_DELAY / 1000) * attempt
        )

        if self._monitor_stop.wait(delay):
            return

        station = self.current_station
        url = self.current_url

        try:
            with self._lock:

                self.player.stop()

                media = self.instance.media_new(url)

                media.add_option(
                    f":network-caching={int(NETWORK_CACHING)}"
                )

                media.add_option(":http-reconnect=true")
                media.add_option(":network-timeout=10000")
                media.add_option(":no-video")

                self.player.set_media(media)

                self.player.audio_set_volume(
                    0 if self._muted else self.volume
                )

                result = self.player.play()

                if result == -1:
                    raise RuntimeError(
                        "VLC не принял поток"
                    )

            self.notify_state("CONNECTING")

        except Exception as error:

            if attempt >= MAX_RECONNECT_ATTEMPTS:
                self.notify_state("ERROR")
                self.notify_error(
                    f"Переподключение не удалось: {error}"
                )

    # ======================================================
    # RESET RECONNECT
    # ======================================================

    def reset_reconnect_attempts(self):
        self.reconnect_attempts = 0

    # ======================================================
    # CLEANUP
    # ======================================================

    def destroy(self):
        """Полностью освобождает VLC."""

        if self._destroyed:
            return

        self._destroyed = True

        # Останавливаем monitor
        self._monitor_stop.set()

        # Останавливаем player
        try:
            self.player.stop()
        except Exception:
            pass

        # Освобождаем player
        try:
            self.player.release()
        except Exception:
            pass

        # Освобождаем VLC instance
        try:
            self.instance.release()
        except Exception:
            pass

        self.current_url = None
        self.current_station = None