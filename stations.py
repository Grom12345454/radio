STATIONS = {
    "ПОПУЛЯРНЫЕ": {
        "Европа Плюс": "http://ep128.hostingradio.ru:8030/ep128",
        "Дорожное Радио": "http://dorognoe.hostingradio.ru:8000/dorognoe",
        "Авторадио": "http://ic2.101.ru:8000/v1_1",
        "Русское Радио": "https://rusradio.hostingradio.ru/rusradio128.mp3",
        "DFM": "http://dfm.hostingradio.ru/dfm96.aacp",
        "Love Radio": "http://ic7.101.ru:8000/v13_1",
        "Хит FM": "http://hitfm.hostingradio.ru/hitfm96.aacp",
    },
    
    "РОК И АЛЬТЕРНАТИВА": {
        "Классический Рок": {
            "Наше Радио": "http://nashe1.hostingradio.ru/nashe-128.mp3",
            "Радио Maximum": "http://maximum.hostingradio.ru/maximum96.aacp",
            "Rock FM": "https://rock.hostingradio.ru/rock96.aacp",
        },
        "Альтернатива": {
            "Radio Record Rock": "https://radiorecord.hostingradio.ru/rock96.aacp",
            "NRJ Rock": "https://nrj.hostingradio.ru/nrjrock96.aacp",
        }
    },
    
    "РЕЛАКС И ЧИЛЛАУТ": {
        "Эмбиент": {
            "Relax FM": "https://stream.laut.fm/relax-fm",
            "Record Relax": "https://radiorecord.hostingradio.ru/rlx96.aacp",
        },
        "Чиллаут": {
            "Record Chillout": "https://radiorecord.hostingradio.ru/chil96.aacp",
            "Chillout Lounge": "https://chillout.hostingradio.ru/chillout96.aacp",
        },
        "Lo-Fi": {
            "Lo-Fi Beats": "https://radiorecord.hostingradio.ru/lofi96.aacp",
            "Record Lo-Fi": "https://radiorecord.hostingradio.ru/lofi96.aacp",
        }
    },
    
    "ТАНЦЕВАЛЬНАЯ": {
        "EDM": {
            "Record Dance": "https://radiorecord.hostingradio.ru/rr_main96.aacp",
            "Record EDM": "https://radiorecord.hostingradio.ru/edm96.aacp",
        },
        "Deep House": {
            "Record Deep": "https://radiorecord.hostingradio.ru/deep96.aacp",
            "House Radio": "https://house.hostingradio.ru/house96.aacp",
        },
        "Хайп": {
            "Record Hip-Hop": "https://radiorecord.hostingradio.ru/hiphop96.aacp",
            "Bass FM": "https://bass.hostingradio.ru/bass96.aacp",
        }
    },
    
    "РЕТРО": {
        "80-90е": {
            "Ретро FM": "http://retroserver.streamr.ru:8043/retro256.mp3",
            "Record 90-х": "https://radiorecord.hostingradio.ru/sd9096.aacp",
        },
        "Ностальгия": {
            "Record 80-х": "https://radiorecord.hostingradio.ru/sd8096.aacp",
            "Disco FM": "https://disco.hostingradio.ru/disco96.aacp",
        }
    },
    
    "ЭЛЕКТРОННАЯ": {
        "Techno": {
            "Record Techno": "https://radiorecord.hostingradio.ru/techno96.aacp",
            "Techno Base": "https://technobase.hostingradio.ru/techno96.aacp",
        },
        "Trance": {
            "Record Trance": "https://radiorecord.hostingradio.ru/trance96.aacp",
            "Pure Trance": "https://puretrance.hostingradio.ru/puretrance96.aacp",
        },
        "Drum & Bass": {
            "Record DnB": "https://radiorecord.hostingradio.ru/dnb96.aacp",
            "DNB FM": "https://dnb.hostingradio.ru/dnb96.aacp",
        }
    },
    
    "ДЖАЗ И БЛЮЗ": {
        "Classic Jazz": {
            "Jazz FM": "https://jazz.hostingradio.ru/jazz96.aacp",
            "Smooth Jazz": "https://smoothjazz.hostingradio.ru/smoothjazz96.aacp",
        },
        "Blues": {
            "Blues Radio": "https://blues.hostingradio.ru/blues96.aacp",
            "Soul FM": "https://soul.hostingradio.ru/soul96.aacp",
        }
    },
    
    "POP И ХИТЫ": {
        "Top Hits": {
            "Record Top 40": "https://radiorecord.hostingradio.ru/top40_96.aacp",
            "Europa Plus TV": "http://ep128.hostingradio.ru:8030/ep128",
        },
        "Dance Pop": {
            "Record Dance": "https://radiorecord.hostingradio.ru/rr_main96.aacp",
            "Energy FM": "https://energy.hostingradio.ru/energy96.aacp",
        }
    }
}


def flatten_stations(stations_dict, parent_category=""):
    flat = {}
    for key, value in stations_dict.items():
        full_name = f"{parent_category} > {key}" if parent_category else key
        if isinstance(value, dict):
            has_urls = any(isinstance(v, str) for v in value.values())
            if has_urls:
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        flat[f"{full_name} > {sub_key}"] = sub_value
                    elif isinstance(sub_value, dict):
                        flat.update(flatten_stations({sub_key: sub_value}, full_name))
            else:
                flat.update(flatten_stations(value, full_name))
        elif isinstance(value, str):
            flat[full_name] = value
    return flat


def get_all_stations_flat():
    return flatten_stations(STATIONS)


def get_categories():
    return list(STATIONS.keys())


def get_stations_by_category(category):
    return STATIONS.get(category, {})


def search_stations(query):
    if not query:
        return get_all_stations_flat()
    
    query_lower = query.lower()
    all_stations = get_all_stations_flat()
    
    filtered = {
        name: url 
        for name, url in all_stations.items() 
        if query_lower in name.lower()
    }
    
    return filtered


def get_nested_structure():
    return STATIONS