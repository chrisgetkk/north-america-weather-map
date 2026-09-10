import csv
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Start with key Midwest / East / PJM / TX sites (can expand later)
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

# Parse CSV -> { site_id: { "YYYY-MM-DDTHH:00": temp_f, ... }, ... }
out = {}
reader = csv.DictReader(io.StringIO(raw))
for row in reader:
    site = (row.get("Site ID") or row.get("SiteId") or "").strip()
    date = (row.get("Valid Date") or "").strip()
    hour = (row.get("Valid Hour") or "").strip()
    temp = row.get("Temp F") or row.get("TempF")
    if not site or not date or not hour or temp in (None, ""):
        continue
    try:
        temp_f = round(float(temp), 1)
    except ValueError:
        continue

    # Normalize hour like "03:00 PM" / "3:00 PM" / "15:00"
    key_time = None
    for fmt in ("%I:%M %p", "%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(hour.strip(), fmt)
            key_time = f"{t.hour:02d}:00"
            break
        except ValueError:
            pass
    if not key_time:
        continue

    # Date like 09/08/2026
    try:
        d = datetime.strptime(date, "%m/%d/%Y")
        day = d.strftime("%Y-%m-%d")
    except ValueError:
        continue

    out.setdefault(site, {})[f"{day}T{key_time}"] = temp_f

payload = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}

Path("data").mkdir(parents=True, exist_ok=True)
path = Path("data/forecast-hourly.json")
path.write_text(json.dumps(payload, indent=2))
print("Wrote", path, "with", len(out), "sites")
