from datetime import datetime
from src import vitals

D = datetime(2026, 6, 6)

def test_gemini_fed_passthrough():
    fed = {"vitals": {"cells": [{"icon": "x", "label": "L", "main": "1", "sub": "s", "status": "good"}],
                      "advisory": {"level": "info", "text": "t"}}}
    assert vitals.build_vitals({}, fed, D) is fed["vitals"]

def test_summer_mock_has_six_cells_and_anchors():
    v = vitals.build_vitals({}, None, D)
    assert v and len(v["cells"]) == 6
    assert v["cells"][0]["label"] == "Weather"
    assert v["cells"][-1]["label"] == "Daylight"
    assert v["advisory"]["text"]

def test_each_season_renders_distinct_cells():
    labels = {m: [c["label"] for c in vitals.build_vitals({}, None, datetime(2026, m, 15))["cells"]]
              for m in (1, 4, 7, 10)}
    assert "Bogus Basin" in labels[1]       # winter
    assert "Pollen" in labels[4]            # spring
    assert "Fire & UV" in labels[7]         # summer
    assert "Cottonwoods" in labels[10]      # fall

def test_all_statuses_valid():
    for m in (1, 4, 7, 10):
        for c in vitals.build_vitals({}, None, datetime(2026, m, 15))["cells"]:
            assert c["status"] in vitals.VALID_STATUS

def test_weather_cell_uses_real_nws_temp():
    raw = {"weather": {"periods": [{"temperature": 61, "temperatureUnit": "F", "shortForecast": "Sunny"}]}}
    v = vitals.build_vitals(raw, None, D)
    assert "61" in v["cells"][0]["main"]
