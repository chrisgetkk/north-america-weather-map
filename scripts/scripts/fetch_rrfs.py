import csv
import io
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

APIKEY = os.environ["STORMVISTA_APIKEY"]
SITE_IDS = [
    "KCMH","KDAY","KCLE","KCVG","KIND","KDTW","KORD","KMDW","KMKE","KMSP",
    "KSTL","KMCI","KPHL","KPIT","KBWI","KDCA","KIAD","KCLT","KRDU","KATL",
    "KBNA","KMEM","KSDF","KJFK","KLGA","KEWR","KBOS","KBUF","KIAH","KHOU",
    "KDFW","KAUS","KSAT","KOKC","KTUL","KMSY","KMIA","KMCO","KTPA","KDEN",
]

# Prefer recent RRFS cycles (every 3h)
def candidate_cycles(now_utc):
    out = []
    base = now_utc.replace(minute=0, second=0, microsecond=0)
    for hours_back in range(0, 18):
        t = base - timedelta(hours=hours_back)
        if t.hour % 3 == 0:
            out.append((t.strftime("%Y%m%d"), f"{t.hour:02d}"))
    return out


def fetch_station(station, date, cycle):
    path = f"/v1/model-data/rrfs/{date}/{cycle}z/city-extraction/individual/{station}_raw.csv"
    url = "https://api.stormvistawxmodels.com" + path + "?" + urllib.parse.urlencode({"apikey": APIKEY})
    req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapRRFS/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_csv(raw):
    # Expect columns including valid time + tmp2m
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for row in reader:
        clean = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        # try common time keys
        traw = clean.get("valid_time") or clean.get("validtime") or clean.get("time") or clean.get("fhour")
        temp = clean.get("tmp2m") or clean.get("temp") or clean.get("t2m")
        if temp in (None, ""):
            continue
        try:
            temp_f = round(float(temp), 1)
        except ValueError:
            continue
        rows.append((clean, temp_f, traw))
    return rows, reader.fieldnames


out = {}
meta = {"model": "rrfs", "cycle": None, "date": None}
Path("data").mkdir(parents=True, exist_ok=True)

now = datetime.now(timezone.utc)
cycles = candidate_cycles(now)
print("Trying cycles:", cycles[:6])

chosen = None
sample_raw = None
for date, cycle in cycles:
    try:
        raw = fetch_station("KCMH", date, cycle)
        if "tmp2m" in raw.lower() or "Temp" in raw or len(raw) > 100:
            chosen = (date, cycle)
            sample_raw = raw
            print("Using cycle", date, cycle, "len", len(raw))
            break
    except Exception as e:
        print("Cycle", date, cycle, "failed:", e)
        time.sleep(0.5)

if not chosen:
    print("No RRFS cycle available")
    payload = {"updated_at": now.isoformat(), "sites": {}, "error": "no cycle"}
    Path("data/rrfs-hourly.json").write_text(json.dumps(payload, indent=2))
    raise SystemExit(0)

date, cycle = chosen
meta["date"] = date
meta["cycle"] = cycle
Path("data/rrfs-raw-sample.txt").write_text(sample_raw[:3000])

# Parse sample headers for debug
try:
    rows, fields = parse_csv(sample_raw)
    print("Fields:", fields)
    print("Sample rows:", len(rows))
except Exception as e:
    print("Parse sample error", e)

for i, station in enumerate(SITE_IDS):
    try:
        raw = fetch_station(station, date, cycle) if station != "KCMH" else sample_raw
        reader = csv.DictReader(io.StringIO(raw))
        site_map = {}
        for row in reader:
            clean = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            temp = clean.get("tmp2m")
            if temp in (None, ""):
                continue
            try:
                temp_f = round(float(temp), 1)
            except ValueError:
                continue
            # Build hour key from valid time if present
            vt = clean.get("valid_time") or clean.get("validtime") or clean.get("time") or ""
            fhr = clean.get("fhour") or clean.get("forecast_hour") or clean.get("hour")
            key = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d%H", "%m/%d/%Y %H:%M"):
                try:
                    dt = datetime.strptime(vt[:19], fmt)
                    key = dt.strftime("%Y-%m-%d") + "T" + f"{dt.hour:02d}:00"
                    break
                except Exception:
                    pass
            if key is None and fhr not in (None, ""):
                try:
                    init = datetime.strptime(date + cycle, "%Y%m%d%H")
                    dt = init + timedelta(hours=int(float(fhr)))
                    key = dt.strftime("%Y-%m-%d") + "T" + f"{dt.hour:02d}:00"
                except Exception:
                    continue
            if key is None:
                continue
            site_map[key] = temp_f
        if site_map:
            out[station] = site_map
        if (i + 1) % 10 == 0:
            print(f"Progress {i+1}/{len(SITE_IDS)} sites={len(out)}")
        time.sleep(0.35)
    except Exception as e:
        print(station, "fail", e)
        time.sleep(0.7)

payload = {
    "updated_at": now.isoformat(),
    "model": "rrfs",
    "date": date,
    "cycle": cycle,
    "forecast_init": f"{date} {cycle}z",
    "sites": out,
}
Path("data/rrfs-hourly.json").write_text(json.dumps(payload, indent=2))
print("Wrote RRFS sites:", len(out))
