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
    "KCMH","KOSU","KLCK","KTZR","KDAY","KCLE","KCAK","KYNG","KTOL","KCVG","KLUK",
    "KIND","KFWA","KSBN","KEVV","KDTW","KDET","KGRR","KLAN","KFNT",
    "KORD","KMDW","KRFD","KPIA","KCMI","KSPI","KMKE","KMSN","KGRB","KMSP","KRST","KDLH",
    "KSTL","KMCI","KSGF","KCOU","KDSM","KCID","KDBQ","KSUX","KOMA","KLNK","KICT","KTOP","KOKC","KTUL",
    "KJFK","KLGA","KEWR","KPHL","KPIT","KBWI","KDCA","KIAD","KRIC","KORF","KROA","KCRW","KHTS",
    "KBOS","KBDL","KPVD","KBUF","KROC","KSYR","KALB",
    "KCLT","KRDU","KGSO","KAVL","KCHS","KCAE","KGSP","KATL","KAHN","KSAV",
    "KBNA","KMEM","KSDF","KLEX","KBHM","KHSV","KMOB","KJAN","KMSY","KBTR",
    "KMIA","KFLL","KMCO","KTPA","KJAX","KPBI","KTLH",
    "KIAH","KHOU","KDFW","KDAL","KAUS","KSAT","KELP","KMAF","KLRD","KCRP","KLIT","KXNA",
    "KDEN","KCOS","KPHX","KTUS","KLAS","KSEA","KPDX","KLAX","KSAN","KSFO","KSJC","KSLC",
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
with urllib.request.urlopen(req, timeout=300) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

Path("data").mkdir(parents=True, exist_ok=True)
Path("data/forecast-raw-sample.txt").write_text(raw[:5000])
print("Response length:", len(raw))

# Find all station headers like: NA-KCMH , Hourly Forecast Made ...
header_re = re.compile(r"NA-([A-Z0-9]{3,4})\s*,\s*Hourly Forecast Made\s+(.+)", re.I)
matches = list(header_re.finditer(raw))
print("Station headers found:", len(matches))

out = {}
init_label = None

for i, m in enumerate(matches):
    site = m.group(1).upper()
    made = m.group(2).strip()
    if init_label is None:
        init_label = made
    start = m.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
    block = raw[start:end]

    lines = block.splitlines()
    header_idx = None
    for j, line in enumerate(lines):
        if "LocalTime" in line and "Temp" in line:
            header_idx = j
            break
    if header_idx is None:
        continue

    table = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(table))
    for row in reader:
        clean = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        local = clean.get("LocalTime", "")
        temp = clean.get("Temp", "")
        if not local or not temp:
            continue
        try:
            temp_f = round(float(temp), 1)
        except ValueError:
            continue
        dt = None
        for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M %p"):
            try:
                dt = datetime.strptime(local, fmt)
                break
            except ValueError:
                pass
        if dt is None:
            continue
        key = dt.strftime("%Y-%m-%d") + "T" + f"{dt.hour:02d}:00"
        out.setdefault(site, {})[key] = temp_f

payload = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "forecast_init": init_label,
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}
Path("data/forecast-hourly.json").write_text(json.dumps(payload, indent=2))
print("Wrote sites:", len(out))
for s, hours in list(out.items())[:8]:
    print(s, "->", len(hours), "hours")
if len(out) < 20:
    print("WARNING: few sites parsed; sample headers:")
    for m in matches[:10]:
        print(" ", m.group(0)[:80])
