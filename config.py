# ============================================================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ============================================================

APP_NAME = "RadioStation"
APP_VERSION = "1.0.0"

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650

MIN_WIDTH = 800
MIN_HEIGHT = 520

DEFAULT_VOLUME = 75

# Сколько VLC ждёт данных перед началом воспроизведения.
# Чем больше значение — тем меньше вероятность заиканий,
# но тем дольше подключение.
NETWORK_CACHING = 1500

# Интервал обновления интерфейса
UI_UPDATE_INTERVAL = 100

# Через сколько проверять подключение
CONNECTION_CHECK_INTERVAL = 1000

# Автоматическое переподключение
AUTO_RECONNECT = True
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY = 3000


# ============================================================
# ЦВЕТА
# ============================================================

BG = "#0D0F13"
PANEL = "#15181E"
PANEL_LIGHT = "#1C2028"
PANEL_HOVER = "#252A34"

ACCENT = "#6C63FF"
ACCENT_HOVER = "#8178FF"

TEXT = "#F5F7FA"
TEXT_SECONDARY = "#B2B8C2"
TEXT_MUTED = "#747C89"

SUCCESS = "#32D583"
WARNING = "#FFB547"
ERROR = "#F97066"

BORDER = "#292E37"
