import vlc

from config import (
    NETWORK_CACHING,
    AUTO_RECONNECT,
    MAX_RECONNECT_ATTEMPTS
)


class RadioPlayer:

    def __init__(self):

        self.instance = vlc.Instance(
            "--no-video",
            "--quiet"
        )

        self.player = self.instance.media_player_new()

        self.current_url = None
        self.current_station = None

        self.volume = 75

        self.reconnect_attempts = 0

        self.on_state_changed = None
        self.on_error = None


    # ========================================================
    # CALLBACK
    # ========================================================

    def set_callbacks(
        self,
        on_state_changed=None,
        on_error=None
    ):

        self.on_state_changed = on_state_changed
        self.on_error = on_error


    def notify_state(self, state):

        if self.on_state_changed:

            try:
                self.on_state_changed(state)
            except Exception:
                pass


    # ========================================================
    # PLAY
    # ========================================================

    def play(self, station_name, url):

        self.stop()

        self.current_station = station_name
        self.current_url = url

        self.reconnect_attempts = 0

        try:

            media = self.instance.media_new(url)

            media.add_option(
                f":network-caching={NETWORK_CACHING}"
            )

            media.add_option(
                ":http-reconnect=true"
            )

            self.player.set_media(media)

            result = self.player.play()

            if result == -1:

                self.notify_state("ERROR")

                if self.on_error:
                    self.on_error(
                        "VLC не смог запустить поток."
                    )

                return False

            self.set_volume(
                self.volume
            )

            self.notify_state(
                "CONNECTING"
            )

            return True

        except Exception as error:

            self.notify_state("ERROR")

            if self.on_error:
                self.on_error(
                    f"Ошибка запуска: {error}"
                )

            return False


    # ========================================================
    # PAUSE / RESUME
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


    def resume(self):

        try:

            self.player.play()

            self.notify_state(
                "PLAYING"
            )

            return True

        except Exception:
            return False


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

        try:
            self.player.stop()
        except Exception:
            pass

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
                min(
                    100,
                    value
                )
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
    # STATUS
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
    # TITLE / METADATA
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

            return title

        except Exception:

            return None


    # ========================================================
    # CLEANUP
    # ========================================================

    def destroy(self):

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
