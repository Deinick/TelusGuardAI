import csv
import json

INPUT_CSV = "./src/data/302.csv"
OUTPUT_JSON = "./src/data/telus_towers.json"

TELUS_MNC = 720     # TELUS
CANADA_MCC = 302

towers = []

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        # Defensive check
        if len(row) < 9:
            continue

        radio = row[0]
        mcc = int(row[1])
        mnc = int(row[2])
        cell_id = row[4]

        lon = float(row[6])
        lat = float(row[7])

        range_m = int(row[8]) if row[8] else None
        samples = int(row[9]) if len(row) > 9 and row[9] else None

        # Keep ONLY TELUS towers in Canada
        if mcc != CANADA_MCC or mnc != TELUS_MNC:
            continue

        towers.append({
            "id": f"{mcc}-{mnc}-{cell_id}",
            "lat": lat,
            "lon": lon,
            "radio": radio,
            "mcc": mcc,
            "mnc": mnc,
            "range": range_m,
            "samples": samples
        })

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(towers, f, indent=2)

print(f"Converted {len(towers)} TELUS towers → {OUTPUT_JSON}")
