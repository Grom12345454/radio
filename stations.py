# ============================================================
# РАДИОСТАНЦИИ РФ (stations_ru.py)
# ============================================================

STATIONS = {
    # ================= ПОПУЛЯРНЫЕ / ХИТЫ =================
    
    "🇷🇺 Европа Плюс": 
        "http://ep128.hostingradio.ru:8030/ep128",

    "🇷🇺 Дорожное Радио": 
        "http://dorognoe.hostingradio.ru:8000/dorognoe",

    "🇷🇺 Авторадио": 
        "http://ic7.101.ru:8000/a15_1",

    "🇷🇺 Love Radio": 
        "http://cast.liveradio.ru/lovetranscode",

    "🇷🇺 Русское Радио": 
        "http://rusradio.hostingradio.ru/rusradio96.aacp",

    "🇷🇺 DFM": 
        "http://dfm.hostingradio.ru/dfm96.aacp",

    "🇷🇺 Energy FM": 
        "http://pub0101.101.ru:8000/stream/air/aes/99/99",

    # ================= РОК И АЛЬТЕРНАТИВА =================

    "🎸 Наше Радио": 
        "http://nashe1.hostingradio.ru/nashe-128.mp3",

    "🎸 Rock FM": 
        "http://rockfm.hostingradio.ru/rockfm96.aacp",

    "🎸 Радио Maximum": 
        "http://maximum.hostingradio.ru/maximum96.aacp",

    "🎸 Радио Джаз": 
        "http://jazz.hostingradio.ru/jazz128.mp3",

    # ================= РЕЛАКС И ФОНОВАЯ МУЗЫКА =================

    "🌊 Relax FM": 
        "http://ic7.101.ru:8000/c15_1",

    "☕ Lounge FM": 
        "http://loungefm.hostingradio.ru/loungefm128.mp3",

    "🍃 Record Chillout": 
        "http://radiorecord.hostingradio.ru/chil96.aacp",

    # ================= ТАНЦЕВАЛЬНАЯ / КЛУБНАЯ =================

    "💃 Record Dance Radio": 
        "http://radiorecord.hostingradio.ru/rr96.aacp",

    "💃 Record Deep": 
        "http://radiorecord.hostingradio.ru/deep96.aacp",

    "💃 Record Trap": 
        "http://radiorecord.hostingradio.ru/trap96.aacp",

    "💃 Record Dubstep": 
        "http://radiorecord.hostingradio.ru/dub96.aacp",

    # ================= НОВОСТИ И РАЗГОВОРНЫЕ =================

    "📰 Вести FM": 
        "http://icecast.vgtrk.com/vestifm_mp3_128kbps",

    "📰 Комсомольская Правда": 
        "http://kp.hostingradio.ru/kp128.mp3",

    "📰 Говорит Москва": 
        "http://govoritmoskva.hostingradio.ru/govoritmoskva128.mp3",

    "📰 Business FM": 
        "http://bfm.hostingradio.ru/bfm96.aacp",
}


def get_stations():
    """Возвращает копию словаря станций."""
    return dict(STATIONS)


def search_stations(query):
    """
    Поиск станций по названию.
    Возвращает список имен станций, содержащих запрос.
    """
    query = query.lower().strip()
    
    if not query:
        return list(STATIONS.keys())
    
    return [
        name for name in STATIONS 
        if query in name.lower()
    ]


def get_url_by_name(name):
    """Получить URL станции по её точному имени."""
    return STATIONS.get(name)