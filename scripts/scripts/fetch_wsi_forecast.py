import csv
import io
import json
import os
import re
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
with urllib.request.urlopen(req, timeout=180) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

Path("data").mkdir(parents=True, exist_ok=True)
Path("data/forecast-raw-sample.txt").write_text(raw[:3000])
print("Response length:", len(raw))
print("Response starts with:", raw[:180].replace("\n", " | "))

out = {}

# WSI returns one or more blocks like:
# NA-KCMH , Hourly Forecast Made ...
# LocalTime, Temp, ...
# 9/10/2026 3:00:00 PM,77.36,...
blocks = re.split(r"(?=NA-[A-Z0-9]+)", raw)
for block in blocks:
    block = block.strip()
    if not block.startswith("NA-"):
        continue

    first_line = block.splitlines()[0]
    m = re.match(r"NA-([A-Z0-9]+)", first_line.strip())
    if not m:
        continue
    site = m.group(1)

    # Find header line and rows after it
    lines = block.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if "LocalTime" in line and "Temp" in line:
            header_idx = i
            break
    if header_idx is None:
        continue

    table = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(table))
    for row in reader:
        local = (row.get("LocalTime") or "").strip()
        temp = row.get("Temp")
        if not local or temp in (None, ""):
            continue
        try:
            temp_f = round(float(temp), 1)
        except ValueError:
            continue

        # Parse "9/10/2026 3:00:00 PM"
        dt = None
        for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M %p"):
            try:
                dt = datetime.strptime(local, fmt)
                break
            except ValueError:
                pass
        if not dt:
            continue

        key = f"{dt.strftime('%Y-%m-%d')}T{dt.hour:02d}:00"
        out.setdefault(site, {})[key] = temp_f

payload = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}
Path("data/forecast-hourly.json").write_text(json.dumps(payload, indent=2))
print("Wrote data/forecast-hourly.json with", len(out), "sites")
if out:
    sample_site = next(iter(out))
    print("Sample site", sample_site, "hours:", len(out[sample_site]))
else:
    print("WARNING: still no sites parsed")
