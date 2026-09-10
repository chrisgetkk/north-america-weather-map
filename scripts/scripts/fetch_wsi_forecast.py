import csv
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SITE_IDS = [
    "KCMH", "KDAY", "KCLE", "KCVG", "KIND", "KFWA",
    "KDTW", "KORD", "KMDW", "KMKE", "KMSP", "KSTL", "KMCI",
    "KPHL", "KPIT", "KBWI", "KDCA", "KIAD", "KRIC",
    "KCLT", "KRDU", "KATL", "KBNA", "KMEM", "KSDF",
    "KJFK", "KLGA", "KEWR", "KBOS", "KBUF",
    "KIAH", "KHOU", "KDFW", "KAUS", "KSAT",
    "KOKC", "KTUL", "KLIT", "KMSY", "KBHM",
]

ACCOUNT = os.environ["WSI_ACCOUNT"]
PROFILE = os.environ["WSI_PROFILE"]
PASSWORD = os.environ["WSI_PASSWORD"]

params = [
    ("Account", ACCOUNT),
    ("Profile", PROFILE),
    ("Password", PASSWORD),
    ("region", "NA"),
    ("TempUnits", "F"),
    ("timeutc", "false"),
]
for site in SITE_IDS:
    params.append(("SiteIds[]", site))

url = "https://www.wsitrader.com/Services/CSVDownloadService.svc/GetHourlyForecast?" + urllib.parse.urlencode(params)

print("Requesting forecast for", len(SITE_IDS), "sites...")
req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapForecastBot/1.0"})
with urllib.request.urlopen(req, timeout=120) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

Path("data").mkdir(parents=True, exist_ok=True)
# Keep a short sample so we can debug if parsing fails
Path("data/forecast-raw-sample.txt").write_text(raw[:2000])
print("Response length:", len(raw))
print("Response starts with:", raw[:200].replace("\n", " | "))

out = {}
reader = csv.DictReader(io.StringIO(raw))
fieldnames = reader.fieldnames or []
print("CSV headers:", fieldnames)

for row in reader:
    # try several possible header names
    site = (
        row.get("Site ID")
        or row.get("SiteId")
        or row.get("Site")
        or row.get("Location")
        or ""
    ).strip()
    date = (row.get("Valid Date") or row.get("Date") or "").strip()
    hour = (row.get("Valid Hour") or row.get("Hour") or "").strip()
    temp = row.get("Temp F") or row.get("TempF") or row.get("Temp")

    if not site or not date or not hour or temp in (None, ""):
        continue

    # If site is a city name, map a few common ones to IDs
    if site.upper() not in [s.upper() for s in SITE_IDS]:
        name_map = {
            "COLUMBUS": "KCMH",
            "CHICAGO": "KORD",
            "INDIANAPOLIS": "KIND",
            "DETROIT": "KDTW",
            "PITTSBURGH": "KPIT",
            "PHILADELPHIA": "KPHL",
            "ATLANTA": "KATL",
            "HOUSTON": "KIAH",
            "DALLAS": "KDFW",
        }
        site = name_map.get(site.upper(), site)

    try:
        temp_f = round(float(temp), 1)
    except ValueError:
        continue

    key_time = None
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(hour.strip(), fmt)
            key_time = f"{t.hour:02d}:00"
            break
        except ValueError:
            pass
    if not key_time:
        continue

    try:
        d = datetime.strptime(date, "%m/%d/%Y")
        day = d.strftime("%Y-%m-%d")
    except ValueError:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            day = d.strftime("%Y-%m-%d")
        except ValueError:
            continue

    out.setdefault(site, {})[f"{day}T{key_time}"] = temp_f

payload = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}
Path("data/forecast-hourly.json").write_text(json.dumps(payload, indent=2))
print("Wrote data/forecast-hourly.json with", len(out), "sites")
if not out:
    print("WARNING: no rows parsed. Check data/forecast-raw-sample.txt")
