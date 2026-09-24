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
    "KCMH",
    "KOSU",
    "KLCK",
    "KTZR",
    "KDAY",
    "KCLE",
    "KCAK",
    "KYNG",
    "KTOL",
    "KCVG",
    "KLUK",
    "KIND",
    "KFWA",
    "KSBN",
    "KEVV",
    "KLAF",
    "KBMI",
    "KDTW",
    "KGRR",
    "KLAN",
    "KFNT",
    "KAZO",
    "KMBS",
    "KORD",
    "KMDW",
    "KRFD",
    "KPIA",
    "KSPI",
    "KMLI",
    "KMKE",
    "KMSN",
    "KGRB",
    "KEAU",
    "KMSP",
    "KRST",
    "KDLH",
    "KFSD",
    "KSTL",
    "KMCI",
    "KSGF",
    "KCOU",
    "KDSM",
    "KCID",
    "KDBQ",
    "KSUX",
    "KOMA",
    "KLNK",
    "KICT",
    "KTOP",
    "KOKC",
    "KTUL",
    "KPHL",
    "KPIT",
    "KMDT",
    "KABE",
    "KAVP",
    "KIPT",
    "KUNV",
    "KLBE",
    "KBFD",
    "KERI",
    "KDUJ",
    "KJST",
    "KAOO",
    "KRDG",
    "KCXY",
    "KBWI",
    "KDCA",
    "KIAD",
    "KADW",
    "KSBY",
    "KILG",
    "KACY",
    "KTTN",
    "KEWR",
    "KJFK",
    "KLGA",
    "KRIC",
    "KORF",
    "KROA",
    "KCHO",
    "KPHF",
    "KCRW",
    "KHTS",
    "KCKB",
    "KBOS",
    "KBDL",
    "KPVD",
    "KBUF",
    "KROC",
    "KSYR",
    "KALB",
    "KCLT",
    "KRDU",
    "KGSO",
    "KAVL",
    "KCHS",
    "KCAE",
    "KGSP",
    "KATL",
    "KSAV",
    "KBNA",
    "KMEM",
    "KSDF",
    "KLEX",
    "KBHM",
    "KHSV",
    "KMOB",
    "KJAN",
    "KMSY",
    "KBTR",
    "KSHV",
    "KLIT",
    "KMIA",
    "KFLL",
    "KMCO",
    "KTPA",
    "KJAX",
    "KPBI",
    "KTLH",
    "KIAH",
    "KHOU",
    "KDFW",
    "KDAL",
    "KAUS",
    "KSAT",
    "KELP",
    "KMAF",
    "KLBB",
    "KAMA",
    "KACT",
    "KTYR",
    "KCRP",
    "KBRO",
    "KLRD",
    "KABI",
    "KSJT",
    "KSPS",
    "KCLL",
    "KDEN",
    "KCOS",
    "KPHX",
    "KTUS",
    "KLAS",
    "KSEA",
    "KPDX",
    "KLAX",
    "KSAN",
    "KSFO",
    "KSJC",
    "KSLC",
]


def candidate_cycles(now_utc):
    # Long RRFS runs only (00/06/12/18z) — out to ~84h, slower to publish
    out = []
    base = now_utc.replace(minute=0, second=0, microsecond=0)
    for hours_back in range(0, 36):
        t = base - timedelta(hours=hours_back)
        if t.hour in (0, 6, 12, 18):
            out.append((t.strftime("%Y%m%d"), f"{t.hour:02d}"))
    return out


def fetch_station(station, date, cycle):
    path = f"/v1/model-data/rrfs/{date}/{cycle}z/city-extraction/individual/{station}_raw.csv"
    url = "https://api.stormvistawxmodels.com" + path + "?" + urllib.parse.urlencode({"apikey": APIKEY})
    req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapRRFS/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def to_eastern_key(dt_utc_naive):
    """Model times are Z/UTC; convert to US/Eastern wall time for graph alignment."""
    from zoneinfo import ZoneInfo
    dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
    dt_east = dt_utc.astimezone(ZoneInfo("America/New_York"))
    return dt_east.strftime("%Y-%m-%d") + "T" + f"{dt_east.hour:02d}:00"


def parse_time_to_key(traw, init_date, init_cycle):
    if not traw:
        return None
    traw = traw.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y%m%d%H",
        "%Y%m%d%H%M",
    ):
        try:
            dt = datetime.strptime(traw[:19], fmt) if len(traw) >= 10 else datetime.strptime(traw, fmt)
            return to_eastern_key(dt)
        except Exception:
            pass
    try:
        fhr = int(float(traw))
        init = datetime.strptime(init_date + init_cycle, "%Y%m%d%H")  # Z cycle
        dt = init + timedelta(hours=fhr)
        return to_eastern_key(dt)
    except Exception:
        return None


def parse_station_csv(raw, station, init_date, init_cycle):
    reader = csv.DictReader(io.StringIO(raw))
    fieldnames = [(f or "").strip() for f in (reader.fieldnames or [])]
    site_map = {}
    time_keys = [
        station, station.upper(), station.lower(),
        "valid_time", "validtime", "time", "fhour", "forecast_hour", "hour", "valid"
    ]
    # also first column
    if fieldnames:
        time_keys.insert(0, fieldnames[0])

    for row in reader:
        clean = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        clean_l = {k.lower(): v for k, v in clean.items()}

        temp = clean_l.get("tmp2m") or clean_l.get("temp")
        if temp in (None, ""):
            continue
        try:
            temp_f = round(float(temp), 1)
        except ValueError:
            continue

        traw = ""
        for tk in time_keys:
            if tk in clean and clean[tk]:
                traw = clean[tk]
                break
            if tk.lower() in clean_l and clean_l[tk.lower()]:
                traw = clean_l[tk.lower()]
                break

        key = parse_time_to_key(traw, init_date, init_cycle)
        if key:
            site_map[key] = temp_f
    return site_map, fieldnames


out = {}
Path("data").mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc)
cycles = candidate_cycles(now)
print("Trying cycles:", cycles[:8])

chosen = None
sample_raw = None
for date, cycle in cycles:
    try:
        raw = fetch_station("KCMH", date, cycle)
        if "tmp2m" in raw.lower() and len(raw) > 50:
            chosen = (date, cycle)
            sample_raw = raw
            print("Using cycle", date, cycle, "len", len(raw))
            print("HEAD:", raw[:250].replace("\n", " | "))
            break
    except Exception as e:
        print("Cycle", date, cycle, "failed:", e)
        time.sleep(0.4)

if not chosen:
    payload = {"updated_at": now.isoformat(), "sites": {}, "error": "no cycle"}
    Path("data/rrfs-hourly.json").write_text(json.dumps(payload, indent=2))
    print("No cycle found")
    raise SystemExit(0)

date, cycle = chosen
Path("data/rrfs-raw-sample.txt").write_text(sample_raw[:4000])
sm, fields = parse_station_csv(sample_raw, "KCMH", date, cycle)
print("Fields:", fields)
print("KCMH parsed hours:", len(sm), list(sm.items())[:3])

for i, station in enumerate(SITE_IDS):
    try:
        raw = sample_raw if station == "KCMH" else fetch_station(station, date, cycle)
        site_map, _ = parse_station_csv(raw, station, date, cycle)
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
if out:
    s0 = next(iter(out))
    print("Example", s0, "->", len(out[s0]), "hours", list(out[s0].items())[:2])
