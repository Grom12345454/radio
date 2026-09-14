STATIONS = {
    " ПОПУЛЯРНЫЕ": {
        "Европа Плюс": "http://ep128.hostingradio.ru:8030/ep128",
        "Дорожное Радио": "http://dorognoe.hostingradio.ru:8000/dorognoe",
        "Авторадио": "http://ic2.101.ru:8000/v1_1",
        "Русское Радио": "https://rusradio.hostingradio.ru/rusradio128.mp3",
        "DFM": "http://dfm.hostingradio.ru/dfm96.aacp",
    },
    "🎸 РОК И АЛЬТЕРНАТИВА": {
        "Наше Радио": "http://nashe1.hostingradio.ru/nashe-128.mp3",
        "Радио Maximum": "http://maximum.hostingradio.ru/maximum96.aacp",
        "Radio Record Rock": "https://radiorecord.hostingradio.ru/rock96.aacp",
    },
    "🌊 РЕЛАКС И ЧИЛЛАУТ": {
        "Relax FM": "https://stream.laut.fm/relax-fm",
        "Record Chillout": "https://radiorecord.hostingradio.ru/chil96.aacp",
        "Lo-Fi": "https://radiorecord.hostingradio.ru/lofi96.aacp",
    },
    "💃 ТАНЦЕВАЛЬНАЯ": {
        "Record Dance": "https://radiorecord.hostingradio.ru/rr_main96.aacp",
        "Record Deep": "https://radiorecord.hostingradio.ru/deep96.aacp",
        "Хайп FM": "http://air.volna.top/HypeFM",
    },
    "📼 РЕТРО": {
        "Ретро FM": "http://retroserver.streamr.ru:8043/retro256.mp3",
        "Record 90-х": "https://radiorecord.hostingradio.ru/sd9096.aacp",
        "Ностальгия FM": "http://nostalgiafm.hostingradio.ru:8000/nostalgiafm.mp3",
    },
}

def get_all_stations_flat():
    flat = {}
    for category, stations in STATIONS.items():
        flat.update(stations)
    return flat

def get_categories():
    return list(STATIONS.keys())

def get_stations_by_category(category):
    return STATIONS.get(category, {})