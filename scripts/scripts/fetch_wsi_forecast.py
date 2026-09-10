import csv
import io
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SITE_IDS = ["KCMH"]  # test one site only

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
print("URL (password hidden)")
print(url.replace(PASSWORD, "***"))

req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapForecastBot/1.0"})
with urllib.request.urlopen(req, timeout=180) as resp:
    raw = resp.read().decode("utf-8", errors="replace")

Path("data").mkdir(parents=True, exist_ok=True)
Path("data/forecast-raw-sample.txt").write_text(raw[:4000])
print("Response length:", len(raw))
print("FIRST 300 CHARS:")
print(raw[:300])
print("---")

out = {}
# Try block parse
if "NA-KCMH" in raw or "LocalTime" in raw:
    # Strip title line(s) and parse as CSV from LocalTime header
    lines = raw.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("LocalTime") or (",Temp," in line.replace(" ", "")):
            header_idx = i
            break
    print("header_idx:", header_idx)
    if header_idx is not None:
        print("header line:", lines[header_idx])
        table = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(table))
        print("fieldnames:", reader.fieldnames)
        count = 0
        for row in reader:
            count += 1
            if count <= 3:
                print("row sample:", dict(row))
            local = (row.get("LocalTime") or row.get("Local Time") or "").strip()
            temp = row.get("Temp") or row.get("Temp F")
            if not local or temp in (None, ""):
                continue
            try:
                temp_f = round(float(str(temp).strip()), 1)
            except ValueError:
                continue
            dt = None
            for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"):
                try:
                    dt = datetime.strptime(local, fmt)
                    break
                except ValueError:
                    pass
            if not dt:
                print("Could not parse time:", local)
                continue
            key = f"{dt.strftime('%Y-%m-%d')}T{dt.hour:02d}:00"
            out.setdefault("KCMH", {})[key] = temp_f
        print("rows seen:", count)

payload = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}
Path("data/forecast-hourly.json").write_text(json.dumps(payload, indent=2))
print("sites count:", len(out))
if out:
    print("KCMH hours:", len(out.get("KCMH", {})))
