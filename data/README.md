# Daten

## Rohdaten (`raw/`)

Unverändert, wie vom Datengeber bereitgestellt. Diese Dateien lesen sowohl `src/build_tegel.py` als auch der Power-BI-Bericht `Grundwasser.pbix`. Neue Daten deshalb mit **gleichem Dateinamen und gleichem Spaltenaufbau** hier ablegen; danach den Bericht in Power BI Desktop öffnen und *Start → Aktualisieren* klicken (Anleitung: [README, Abschnitt Power-BI-Bericht](../README.md#power-bi-bericht)).

### `Grundwasser je messstation im zeitverlauf.csv`
Quelle: FUTR HUB, Urban Tech Republic. Komma-getrennt, Dezimalpunkt.

| Spalte | Bedeutung |
|---|---|
| `time_index` | Datum mit Uhrzeit und Zeitzone (`2025-03-01 00:00:00+00:00`), ein Wert pro Tag |
| `gwm…` | Grundwasserstand der Messstelle in Metern (laut Datensatz); leere Zelle = kein Messwert |

Zeitraum 01.03.2025–22.09.2026, 10 Messstellen. Verwendet werden die 8 Messstellen aus der Stationsliste.

### `Karte mit Grundwasserpegel.csv`
Quelle: FUTR HUB, Urban Tech Republic.

| Spalte | Bedeutung |
|---|---|
| `latitude`, `longitude` | Lage der Messstelle, WGS 84 |
| `sensorid` | Name der Messstelle |
| `Wasserpegel [m]` | Grundwasserstand am 22.09.2026 (m) |

### `Niederschlag_Flughafen_Tegel_2025_2026_v6-1_taeglich.csv`
Quelle: Deutscher Wetterdienst, HYRAS-DE-PR. Semikolon-getrennt, **Dezimalkomma**.

| Spalte | Bedeutung |
|---|---|
| `Datum` | Tag (ISO 8601) |
| `Niederschlag_mm` | Tagesniederschlag in mm (1 mm = 1 Liter pro m²) |
| `HYRAS_Latitude`, `HYRAS_Longitude` | Rasterpunkt (52,5615° N, 13,2822° O) |
| `HYRAS_x`, `HYRAS_y` | Rasterkoordinaten |
| `Anzahl_Stationen` | Anzahl der Stationen, die in die Interpolation eingingen |
| `HYRAS_Version` | Datensatzversion, hier nur `v6-1` |
| `Datenstatus` | Prüfstatus des DWD |

Zeitraum 01.01.2025–22.09.2026, ein Wert pro Tag.

## Aufbereitete Daten (`processed/`)

Vom Skript `src/build_tegel.py` erzeugt. Alle Dateien: UTF-8, Komma-getrennt, Dezimalpunkt, Datum `YYYY-MM-DD`, Zeitraum 01.03.2025–22.09.2026. Lizenz: CC BY 4.0 (Quellen der Rohdaten nennen).

### `niederschlag_tegel_taeglich.csv`
| Spalte | Einheit | Bedeutung |
|---|---|---|
| `datum` | – | Tag |
| `niederschlag_mm` | mm | Tagesniederschlag |

### `niederschlag_tegel_monatlich.csv`
| Spalte | Einheit | Bedeutung |
|---|---|---|
| `monat` | – | Monat (`YYYY-MM`); September 2026 nur bis 22.09. |
| `niederschlag_mm` | mm | Monatssumme |

### `grundwasser_tegel_taeglich.csv` (Long-Format)
| Spalte | Einheit | Bedeutung |
|---|---|---|
| `datum` | – | Tag |
| `messstelle` | – | Name der Messstelle |
| `pegel_m` | m | Grundwasserstand |
| `aenderung_seit_start_m` | m | Änderung gegenüber dem ersten Messwert ab 01.03.2025 |

Tage ohne Messwert sind nicht enthalten.

### `grundwasser_aenderung_zeitraeume.csv`
| Spalte | Einheit | Bedeutung |
|---|---|---|
| `zeitraum` | – | `A_trockenes_fruehjahr`, `B_nach_nassem_juli`, `C_nach_19_april_2026`, `gesamt` |
| `von`, `bis` | – | Zeitraum |
| `messstelle` | – | Messstelle oder `MEDIAN` (Median der 8 Messstellen) |
| `aenderung_m` | m | letzter minus erster verfügbarer Wert im Zeitraum |

### `korrelation_regen_grundwasser_verschiebung.csv`
| Spalte | Bedeutung |
|---|---|
| `verschiebung_tage` | Verschiebung der 30-Tage-Regensumme (0–42 Tage) |
| `r_mittelwert` | Pearson-r mit dem Mittelwert der 30-Tage-Änderung aller Messstellen |
| `r_median` | Pearson-r mit dem Median der 30-Tage-Änderung aller Messstellen |
| `r_je_messstelle_median` | Pearson-r je Messstelle berechnet, davon der Median |

### `messstellen.geojson`
Punkte (EPSG:4326) mit den Eigenschaften `messstelle`, `pegel_m_22_09_2026`, `pegel_m_01_03_2025`, `aenderung_gesamt_m`. Direkt nutzbar in QGIS, uMap, Kepler.gl oder Leaflet.

### `website_daten.json`
Alle Werte, die in die Website eingebettet werden (Zeitreihen, Zeiträume, Korrelation, Messstellen).

## OpenStreetMap-Auszug (`osm/tegel_osm.geojson`)

Abgefragt über die Overpass-API, Datenstand 01.06.2026, vereinfacht (Koordinaten auf 5 Nachkommastellen). Eigenschaft `k` = Objektart (`airport`, `runway`, `taxiway`, `apron`, `terminal`, `water`, `park`, `road`), `n` = Name.
Lizenz: © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).
