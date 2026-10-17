"""BPI Challenge 2019 XES -> two parquet tables (cases, events)."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "BPI_Challenge_2019.xes"
OUT = ROOT / "data" / "processed"
ATTR = ["Purchasing Document", "Item", "Item Type", "GR-Based Inv. Verif.", "Goods Receipt", "Source",
        "Purch. Doc. Category name", "Company", "Spend classification text", "Spend area text",
        "Sub spend area text", "Vendor", "Name", "Document Type", "Item Category"]


def parse(path=SRC):
    cases, events = [], []
    case, in_event = None, False
    try:
        for ev, el in ET.iterparse(path, events=("start", "end")):
            tag = el.tag
            if ev == "start":
                if tag == "trace":
                    case = {}
                elif tag == "event":
                    in_event = True
                continue
            if tag == "event":
                a = {c.get("key"): c.get("value") for c in el}
                events.append((case["concept:name"], a.get("concept:name"), a.get("time:timestamp"),
                               a.get("User"), a.get("Cumulative net worth (EUR)")))
                in_event = False
                el.clear()
            elif tag == "trace":
                cases.append(case); case = None; el.clear()
            elif case is not None and not in_event and tag in ("string", "boolean"):
                case[el.get("key")] = el.get("value")
    except ET.ParseError:
        print("file truncated: parsed what was there", file=sys.stderr)
    return cases, events


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cases, events = parse()
    c = pd.DataFrame(cases).rename(columns={"concept:name": "case_id"})
    c = c[["case_id"] + ATTR]
    e = pd.DataFrame(events, columns=["case_id", "activity", "ts", "user", "net_worth"])
    e["ts"] = pd.to_datetime(e.ts, utc=True).dt.tz_localize(None)
    e["net_worth"] = e.net_worth.astype(float)
    e["seq"] = e.groupby("case_id").cumcount()
    c.to_parquet(OUT / "cases.parquet"); e.to_parquet(OUT / "events.parquet")
    print(len(c), "cases", len(e), "events")
