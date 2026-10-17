"""Each SQL test must flag exactly the cases planted for it and nothing else (small hand-built log)."""
import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_tests

ATTR = ["Purchasing Document", "Item", "Item Type", "GR-Based Inv. Verif.", "Goods Receipt", "Source",
        "Purch. Doc. Category name", "Company", "Spend classification text", "Spend area text",
        "Sub spend area text", "Vendor", "Name", "Document Type", "Item Category"]
cases, events = [], []


def case(cid, vendor, user, steps, value=5000.0, po="2018-03-01", grbased="false", item_type="Standard"):
    cases.append(dict(zip(["case_id"] + ATTR, [cid, f"doc_{cid}", "1", item_type, grbased, "true", "s", "po", "c1",
                                               "x", "x", "x", vendor, "n", "d", "3-way match"])))
    t = pd.Timestamp(po)
    events.append((cid, "Create Purchase Order Item", t, user, value))
    for k, (act, who) in enumerate(steps, 1):
        events.append((cid, act, t + pd.Timedelta(days=k), who, value))


GR, IR, CL, CIR = "Record Goods Receipt", "Record Invoice Receipt", "Clear Invoice", "Cancel Invoice Receipt"
case("A", "v1", "user_001", [(GR, "user_002"), (IR, "user_003"), (CL, "user_004")])      # clean
case("B", "v2", "user_010", [(IR, "user_003"), (CL, "user_004")])                         # T1a: paid, no receipt
case("C", "v3", "user_011", [(IR, "user_003"), (CIR, "user_003"), (CL, "user_004")])      # reversal: not T1a
case("D", "v4", "user_012", [(IR, "user_003"), (CL, "user_004"), (GR, "user_002")])       # T4: paid before receipt
case("E", "v5", "user_013", [(GR, "user_013"), (IR, "user_003"), (CL, "user_004")])       # T3: same user orders and receives
case("F", "v9", "user_014", [(GR, "user_002"), (IR, "user_003"), (CL, "user_004")], value=2000.0, po="2018-04-01")
case("G", "v9", "user_015", [(GR, "user_002"), (IR, "user_003"), (CL, "user_004")], value=2000.0, po="2018-04-03")  # T2
case("H", "v6", "user_007", [(GR, "user_002"), (IR, "user_003"), (CL, "user_004")], value=6000.0, po="2018-05-01")
case("I", "v6", "user_007", [(GR, "user_002"), (IR, "user_003"), (CL, "user_004")], value=5000.0, po="2018-05-01")  # T5 pair
case("J", "v7", "user_016", [(IR, "user_003"), (GR, "user_002")], grbased="true")         # T1b: invoice before receipt


def flagged(c, t):
    return set(c.sql(f"select case_id from ex_{t}").df().case_id)


def test_each_test_flags_only_its_planted_cases():
    c = duckdb.connect()
    c.register("cases_df", pd.DataFrame(cases))
    c.register("events_df", pd.DataFrame(events, columns=["case_id", "activity", "ts", "user", "net_worth"]))
    c.execute("create table cases as select * from cases_df")
    c.execute("create table events as select * from events_df")
    run_tests.run_sql(c)
    assert flagged(c, "T1a") == {"B"}
    assert flagged(c, "T1b") == {"J"}
    assert flagged(c, "T2") == {"G"}
    assert flagged(c, "T3") == {"E"}
    assert flagged(c, "T4") == {"D"}
    assert flagged(c, "T5") == {"H", "I"}
