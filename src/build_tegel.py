"""Vom Rollfeld zur Schwammstadt - data analysis and website build.

Run from the repository root:
    python src/build_tegel.py

Reads:
    data/raw/Niederschlag_Flughafen_Tegel_2025_2026_v6-1_taeglich.csv
    data/raw/Grundwasser je messstation im zeitverlauf.csv
    data/raw/Karte mit Grundwasserpegel.csv
    data/osm/tegel_osm.geojson
Writes:
    data/processed/*.csv, *.geojson, *.json   (processed data)
    docs/index.html                           (website for GitHub Pages, photos from docs/img/)
    docs/tegel-datastory-einzeldatei.html     (single file, photos loaded from Wikimedia Commons)
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OSM_FILE = ROOT / "data" / "osm" / "tegel_osm.geojson"
WEB_SRC = ROOT / "src" / "web"
DOCS = ROOT / "docs"

RAIN_FILE = RAW / "Niederschlag_Flughafen_Tegel_2025_2026_v6-1_taeglich.csv"
GW_FILE = RAW / "Grundwasser je messstation im zeitverlauf.csv"
MAP_FILE = RAW / "Karte mit Grundwasserpegel.csv"

START, END = "2025-03-01", "2026-09-22"
HYRAS_VERSION = "v6-1"
EPISODES = [
    ("A_trockenes_fruehjahr", "2025-03-01", "2025-04-30"),
    ("B_nach_nassem_juli", "2025-07-10", "2025-08-20"),
    ("C_nach_19_april_2026", "2026-04-19", "2026-06-19"),
    ("gesamt", START, END),
]

# online photo URLs for the single file version
COMMONS = "https://upload.wikimedia.org/wikipedia/commons"
ONLINE_IMAGES = {
    "img/hero-2019.jpg": f"{COMMONS}/thumb/7/7a/Berlin_Tegel_Airport_%28TXL%29_-_April_2019_%282%29.jpg/1280px-Berlin_Tegel_Airport_%28TXL%29_-_April_2019_%282%29.jpg",
    "img/runway-2015.jpg": f"{COMMONS}/thumb/1/15/Berlin_Tegel_runway_2015.jpg/1280px-Berlin_Tegel_runway_2015.jpg",
    "img/landebahn-2022.jpg": f"{COMMONS}/thumb/8/82/Flughafen_TXL_Landebahn_S%C3%BCd.jpg/1280px-Flughafen_TXL_Landebahn_S%C3%BCd.jpg",
    "img/terminal-a-2022.jpg": f"{COMMONS}/thumb/4/40/Flughafen_TXL_Terminal_A.jpg/1280px-Flughafen_TXL_Terminal_A.jpg",
    "img/terminal-2005.jpg": f"{COMMONS}/a/af/Berlin-Tegel_from_the_air.jpg",
    "img/aerial-2019-see.jpg": f"{COMMONS}/thumb/6/6d/Berliner_Flughafen_Tegel_von_oben_02.jpg/1280px-Berliner_Flughafen_Tegel_von_oben_02.jpg",
}


def load_rain():
    r = pd.read_csv(RAIN_FILE, sep=";", decimal=",", encoding="utf-8-sig")
    if "HYRAS_Version" in r.columns and r["HYRAS_Version"].nunique() > 1:
        # raw file can contain two HYRAS versions, keep only v6-1 so no day is counted twice
        r = r[r["HYRAS_Version"] == HYRAS_VERSION]
    r["Datum"] = pd.to_datetime(r["Datum"])
    if r["Datum"].duplicated().any():
        sys.exit(f"Fehler: doppelte Tage in {RAIN_FILE.name}")
    return r.set_index("Datum")["Niederschlag_mm"].sort_index()


def load_groundwater():
    g = pd.read_csv(GW_FILE)
    g["t"] = pd.to_datetime(g["time_index"].str[:10])
    return g.set_index("t").drop(columns="time_index")


def to_list(series, digits):
    return [None if pd.isna(v) else round(float(v), digits) for v in series]


def change_m(g8, a, b):
    # per station: last minus first available value in the period (m)
    va = g8.loc[a:].bfill().iloc[0]
    vb = g8.loc[:b].ffill().iloc[-1]
    return [round(float(v), 3) for v in (vb - va)]


def lag_curves(rain, gi, stations):
    # pearson r of 30 day rain sum (shifted by lag days) vs. 30 day groundwater change
    r30 = rain.rolling(30).sum()
    corr = lambda y, lag: pd.concat([r30.shift(lag), y], axis=1).dropna().corr().iloc[0, 1]
    d30 = gi.diff(30)
    return {
        "median": [round(corr(d30.median(axis=1), l), 3) for l in range(43)],
        "mean": [round(corr(d30.mean(axis=1), l), 3) for l in range(43)],
        "per": [round(float(pd.Series([corr(d30[s], l) for s in stations]).median()), 3) for l in range(43)],
    }


def build_data():
    rain = load_rain()
    g = load_groundwater()
    m = pd.read_csv(MAP_FILE)
    stations = m["sensorid"].tolist()
    missing = [s for s in stations if s not in g.columns]
    if missing:
        sys.exit(f"Fehler: Messstellen fehlen in der Zeitreihe: {missing}")

    idx = pd.date_range(START, END)
    g8 = g[stations].reindex(idx)
    base = g8.bfill().iloc[0]
    gi = g8.interpolate(limit=5)
    rain_p = rain.reindex(idx)

    data = {
        "start": START,
        "rain": to_list(rain_p, 1),
        "gw": {s: to_list(g8[s] - base[s], 3) for s in stations},
        "gwAbs": {s: to_list(g8[s], 3) for s in stations},
        "median": to_list((gi - base).median(axis=1), 4),
        "lag": lag_curves(rain, gi, stations),
        "monthly": [[k.strftime("%Y-%m"), round(float(v), 1)] for k, v in rain_p.resample("ME").sum().items()],
        "episodes": [change_m(g8, a, b) for _, a, b in EPISODES],
        "stations": [{"id": s, "lat": float(la), "lon": float(lo), "level": float(lv), "start": round(float(base[s]), 2)}
                     for s, la, lo, lv in zip(m["sensorid"], m["latitude"], m["longitude"], m["Wasserpegel [m]"])],
    }
    return data, rain_p, g8, m


def export_processed(data, rain_p, g8, m):
    PROCESSED.mkdir(parents=True, exist_ok=True)
    stations = [s["id"] for s in data["stations"]]
    csv = dict(index=False, encoding="utf-8", lineterminator="\n")

    rain_df = pd.DataFrame({"datum": rain_p.index.strftime("%Y-%m-%d"), "niederschlag_mm": rain_p.values})
    rain_df.to_csv(PROCESSED / "niederschlag_tegel_taeglich.csv", **csv)

    pd.DataFrame(data["monthly"], columns=["monat", "niederschlag_mm"]).to_csv(PROCESSED / "niederschlag_tegel_monatlich.csv", **csv)

    base = g8.bfill().iloc[0]
    long = (g8.rename_axis("datum").reset_index().melt(id_vars="datum", var_name="messstelle", value_name="pegel_m")
              .dropna().sort_values(["messstelle", "datum"]))
    long["aenderung_seit_start_m"] = (long["pegel_m"] - long["messstelle"].map(base)).round(3)
    long["datum"] = long["datum"].dt.strftime("%Y-%m-%d")
    long.to_csv(PROCESSED / "grundwasser_tegel_taeglich.csv", **csv)

    rows = []
    for (name, a, b), vals in zip(EPISODES, data["episodes"]):
        for s, v in zip(stations, vals):
            rows.append({"zeitraum": name, "von": a, "bis": b, "messstelle": s, "aenderung_m": v})
        rows.append({"zeitraum": name, "von": a, "bis": b, "messstelle": "MEDIAN", "aenderung_m": round(float(pd.Series(vals).median()), 4)})
    pd.DataFrame(rows).to_csv(PROCESSED / "grundwasser_aenderung_zeitraeume.csv", **csv)

    lag = pd.DataFrame({"verschiebung_tage": range(43), "r_mittelwert": data["lag"]["mean"],
                        "r_median": data["lag"]["median"], "r_je_messstelle_median": data["lag"]["per"]})
    lag.to_csv(PROCESSED / "korrelation_regen_grundwasser_verschiebung.csv", **csv)

    feats = [{"type": "Feature",
              "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
              "properties": {"messstelle": s["id"], "pegel_m_22_09_2026": s["level"], "pegel_m_01_03_2025": s["start"],
                             "aenderung_gesamt_m": data["episodes"][-1][k]}}
             for k, s in enumerate(data["stations"])]
    (PROCESSED / "messstellen.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")

    (PROCESSED / "website_daten.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def check_numbers(data, rain_p, g8):
    med = lambda v: float(pd.Series(v).median())
    s32 = g8["gwm32-22-op"]
    got = {
        "Regen März+April 2025 (17,8 mm)": (rain_p["2025-03-01":"2025-04-30"].sum(), 17.8, 0.06),
        "Regen Juli 2025 (118 mm)": (rain_p["2025-07"].sum(), 118.0, 0.06),
        "Regen 10.-23.07.2025 (100,6 mm)": (rain_p["2025-07-10":"2025-07-23"].sum(), 100.6, 0.06),
        "Regen 17.-23.07.2025 (58,4 mm)": (rain_p["2025-07-17":"2025-07-23"].sum(), 58.4, 0.06),
        "Max. 30-Tage-Summe (131,6 mm)": (rain_p.rolling(30).sum().max(), 131.6, 0.06),
        "Max. Tageswert (40,7 mm)": (rain_p.max(), 40.7, 0.06),
        "Regen 19.04.-19.06.2026 (101,3 mm)": (rain_p["2026-04-19":"2026-06-19"].sum(), 101.3, 0.06),
        "Regen gesamt (675,9 mm)": (rain_p.sum(), 675.9, 0.06),
        "Grundwasser Median Frühjahr 2025 (-0,183 m)": (med(data["episodes"][0]), -0.183, 0.0006),
        "Grundwasser Median 10.07.-20.08.2025 (+0,0865 m)": (med(data["episodes"][1]), 0.0865, 0.0006),
        "Grundwasser Median 19.04.-19.06.2026 (+0,0705 m)": (med(data["episodes"][2]), 0.0705, 0.0006),
        "Grundwasser Median gesamt (-0,425 m)": (med(data["episodes"][3]), -0.425, 0.0006),
        "Schwankung gwm32-22-op (2,1 m)": (s32.max() - s32.min(), 2.126, 0.06),
    }
    ok = True
    for name, (value, expected, tol) in got.items():
        hit = abs(value - expected) < tol
        ok &= hit
        print(f"  {'OK ' if hit else 'ABWEICHUNG'}  {name}: berechnet {value:.4f}")
    if not ok:
        print("\nAchtung: Mindestens eine Zahl im Text passt nicht mehr zu den Daten. Texte in src/web/template.html anpassen.")
    return ok


def build_site(data):
    html = (WEB_SRC / "template.html").read_text(encoding="utf-8")
    html = (html.replace("__LEAFLET_CSS__", (WEB_SRC / "leaflet.css").read_text(encoding="utf-8"))
                .replace("__DATA__", json.dumps(data, separators=(",", ":")))
                .replace("__GEO__", OSM_FILE.read_text(encoding="utf-8"))
                .replace("__RAINFILE__", RAIN_FILE.name))
    (DOCS / "index.html").write_text(html, encoding="utf-8")

    single = html
    for local, url in ONLINE_IMAGES.items():
        single = single.replace(f'src="{local}"', f'src="{url}" referrerpolicy="no-referrer"')
    (DOCS / "tegel-datastory-einzeldatei.html").write_text(single, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for f in (RAIN_FILE, GW_FILE, MAP_FILE, OSM_FILE):
        if not f.exists():
            sys.exit(f"Datei nicht gefunden: {f}")
    print(f"Lese Rohdaten aus: {RAW}")
    data, rain_p, g8, m = build_data()
    print("Prüfe Zahlen im Text:")
    check_numbers(data, rain_p, g8)
    export_processed(data, rain_p, g8, m)
    print(f"Aufbereitete Daten: {PROCESSED}")
    build_site(data)
    print(f"Website: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
