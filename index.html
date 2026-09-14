import csv
import io
import json
import os
import re
import time
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

BATCH_SIZE = 5
ACCOUNT = os.environ["WSI_ACCOUNT"]
PROFILE = os.environ["WSI_PROFILE"]
PASSWORD = os.environ["WSI_PASSWORD"]
header_re = re.compile(r"NA-([A-Z0-9]{3,4})\s*,\s*Hourly Forecast Made\s+(.+)", re.I)


def fetch_batch(sites):
    params = [
        ("Account", ACCOUNT),
        ("Profile", PROFILE),
        ("Password", PASSWORD),
        ("region", "NA"),
        ("TempUnits", "F"),
        ("timeutc", "false"),
    ]
    for site in sites:
        params.append(("SiteIds[]", site))
    url = "https://www.wsitrader.com/Services/CSVDownloadService.svc/GetHourlyForecast?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "WeatherMapForecastBot/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_raw(raw, out):
    init_label = None
    matches = list(header_re.finditer(raw))
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
    return init_label


out = {}
init_label = None
Path("data").mkdir(parents=True, exist_ok=True)
Path("data/archive").mkdir(parents=True, exist_ok=True)

batches = [SITE_IDS[i:i + BATCH_SIZE] for i in range(0, len(SITE_IDS), BATCH_SIZE)]
print("Total sites:", len(SITE_IDS), "batches:", len(batches))

for n, batch in enumerate(batches, 1):
    try:
        raw = fetch_batch(batch)
        if n == 1:
            Path("data/forecast-raw-sample.txt").write_text(raw[:4000])
        label = parse_raw(raw, out)
        if init_label is None and label:
            init_label = label
        print(f"Batch {n}/{len(batches)}: total sites now {len(out)}")
        time.sleep(1.0)
    except Exception as e:
        print(f"Batch {n} failed:", e)
        time.sleep(2.0)

now = datetime.now(timezone.utc)
payload = {
    "updated_at": now.isoformat(),
    "forecast_init": init_label,
    "run_date": now.strftime("%Y-%m-%d"),
    "source": "WSI Trader Hourly Forecast",
    "sites": out,
}

text = json.dumps(payload, indent=2)
Path("data/forecast-hourly.json").write_text(text)
# Archive by UTC run date (yesterday's file used next day for day-ahead verify)
archive_path = Path("data/archive") / f"forecast-{now.strftime('%Y-%m-%d')}.json"
archive_path.write_text(text)
print("Wrote sites:", len(out))
print("Archived:", archive_path)
