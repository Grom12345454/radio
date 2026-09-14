# stations.py

STATIONS = {
    "ПОПУЛЯРНЫЕ": {
        "Европа Плюс": "http://ep128.hostingradio.ru:8030/ep128",
        "Дорожное Радио": "http://dorognoe.hostingradio.ru:8000/dorognoe",
        "Авторадио": "http://ic2.101.ru:8000/v1_1",
        "Русское Радио": "https://rusradio.hostingradio.ru/rusradio128.mp3",
        "DFM": "http://dfm.hostingradio.ru/dfm96.aacp",
    },

    "РОК И АЛЬТЕРНАТИВА": {
        "Наше Радио": "http://nashe1.hostingradio.ru/nashe-128.mp3",
        "Радио Maximum": "http://maximum.hostingradio.ru/maximum96.aacp",
        "Radio Record Rock": "https://radiorecord.hostingradio.ru/rock96.aacp",
    },

    "РЕЛАКС И ЧИЛЛАУТ": {
        "Relax FM": "https://stream.laut.fm/relax-fm",
        "Record Chillout": "https://radiorecord.hostingradio.ru/chil96.aacp",
    },

    "ТАНЦЕВАЛЬНАЯ": {
        "Record Dance": "https://radiorecord.hostingradio.ru/rr_main96.aacp",
        "Record Deep": "https://radiorecord.hostingradio.ru/deep96.aacp",
        "Хайп FM": "http://air.volna.top/HypeFM",
    },

    "РЕТРО": {
        "Ретро FM": "http://retroserver.streamr.ru:8043/retro256.mp3",
        "Record 90-х": "https://radiorecord.hostingradio.ru/sd9096.aacp",
        "Ностальгия FM": "http://nostalgiafm.hostingradio.ru:8000/nostalgiafm.mp3",
    },

    "ДЖАЗ И БЛЮЗ": {
        "Jazz FM": "http://jazz.streamr.ru/jazz-64.mp3",
        "Smooth Jazz": "http://smoothjazz.com/smoothjazz_128.mp3",
    },

    "Lofi Girl 24/7": {
        "Hip hop": "https://www.youtube.com/watch?v=rFZHOHl-L8A",
        "Lo-Fi": "https://radiorecord.hostingradio.ru/lofi96.aacp",
    },
}

def get_categories():
    return list(STATIONS.keys())

def get_stations_by_category(category_name):
    return STATIONS.get(category_name, {})

def search_stations(query):
    query_lower = query.lower()
    results = []
    for cat_name, stations in STATIONS.items():
        for station_name in stations.keys():
            if query_lower in station_name.lower():
                results.append(station_name)
    return results