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
print("Requesting", len(SITE_IDS), "sites...")

req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapForecastBot/1.0"})
with urllib.request.urlopen(req, timeout=180) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

Path("data").mkdir(parents=True, exist_ok=True)
Path("data/forecast-raw-sample.txt").write_text(raw[:3000])
print("Response length:", len(raw))

out = {}

# Split into station blocks starting with NA-KXXX
parts = raw.split("NA-")
for part in parts[1:]:
    first_line, _, rest = part.partition("\n")
    site = first_line.split()[0].split(",")[0].strip()  # KCMH
    if not site:
        continue

    lines = rest.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if "LocalTime" in line and "Temp" in line:
            header_idx = i
            break
    if
