"""Run after run_tests.py: the log ties to the published totals and every test table ties to the results."""
import json
from pathlib import Path
import pandas as pd

P = Path(__file__).resolve().parents[1] / "data" / "processed"
st = json.load(open(P / "stats.json")); res = pd.read_csv(P / "results.csv").set_index("test")
assert (st["cases"], st["events"], st["docs"], st["users"]) == (251734, 1595923, 76349, 607), "log does not match the published totals"
for t in res.index:
    e = pd.read_parquet(P / f"ex_{t}.parquet")
    assert len(e) == res.loc[t, "exceptions"] and e.case_id.is_unique, t
    assert e.item_value.sum() == res.loc[t, "value"], t
assert st["t3_pairs"].get("PO + goods receipt", 0) == res.loc["T3", "exceptions"], "SoD pairs do not tie"
print("all checks passed")
