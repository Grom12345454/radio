# ============================================================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ============================================================

APP_NAME = "RadioStation 3D"
APP_VERSION = "2.0.0"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750

MIN_WIDTH = 900
MIN_HEIGHT = 600

DEFAULT_VOLUME = 75

# Сколько VLC ждёт данных перед началом воспроизведения
NETWORK_CACHING = 1500

# Интервал обновления интерфейса
UI_UPDATE_INTERVAL = 50

# Через сколько проверять подключение
CONNECTION_CHECK_INTERVAL = 1000

# Автоматическое переподключение
AUTO_RECONNECT = True
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY = 3000

# ============================================================
# ЦВЕТА (3D тема)
# ============================================================

BG = "#0a0e17"
PANEL = "#111827"
PANEL_LIGHT = "#1f2937"
PANEL_HOVER = "#374151"

ACCENT = "#3b82f6"
ACCENT_HOVER = "#60a5fa"
ACCENT_GRADIENT_START = "#3b82f6"
ACCENT_GRADIENT_END = "#8b5cf6"

TEXT = "#f9fafb"
TEXT_SECONDARY = "#d1d5db"
TEXT_MUTED = "#9ca3af"

SUCCESS = "#10b981"
WARNING = "#f59e0b"
ERROR = "#ef4444"

BORDER = "#374151"
SHADOW = "rgba(0, 0, 0, 0.3)"

# 3D эффекты
DEPTH_LEVELS = [
    "#1f2937",  # level 1
    "#111827",  # level 2
    "#0a0e17",  # level 3
]

GLOW_COLOR = "#3b82f6"
GLOW_INTENSITY = 0.5