"""Runs the SQL tests in sql/ on the parsed log; writes results + exception tables."""
from pathlib import Path
import duckdb, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
TESTS = ["T1a", "T1b", "T2", "T3", "T4", "T5"]


def connect():
    c = duckdb.connect()
    c.execute(f"create table events as select * from '{P}/events.parquet'")
    c.execute(f"create table cases as select * from '{P}/cases.parquet'")
    for f in sorted((ROOT / "sql").glob("*.sql")):
        for stmt in f.read_text().split(";\n"):
            if stmt.strip():
                c.execute(stmt)
    return c


def results(c):
    rows = []
    for t in TESTS:
        n = c.sql(f"select n from pop_{t}").fetchone()[0]
        e, v = c.sql(f"select count(*), coalesce(sum(item_value),0) from ex_{t}").fetchone()
        rows.append(dict(test=t, population=n, exceptions=e, rate=e / n if n else 0, value=v))
    return pd.DataFrame(rows)


def stats(c):
    q = lambda sql: c.sql(sql).fetchone()
    d = {}
    d["cases"], d["events"] = q("select count(*), (select count(*) from events) from cases")
    d["docs"] = q("select count(distinct doc) from item_facts")[0]
    d["first"], d["last"] = [str(x)[:10] for x in q("select min(ts), max(ts) from events")]
    d["users"] = q("select count(distinct \"user\") filter (where \"user\" like 'user\\_%' escape '\\') from events")[0]
    d["req_items"] = q("select count(distinct case_id) from events where activity = 'Create Purchase Requisition Item'")[0]
    d["clear_events"] = q("select count(*) from events where activity = 'Clear Invoice'")[0]
    u, n = q("select \"user\", count(*) from events where activity = 'Clear Invoice' group by 1 order by 2 desc limit 1")
    d["top_clear_user"], d["top_clear_n"] = u, n
    d["max_clear_minute"] = q("select max(n) from (select count(*) n from events where activity='Clear Invoice' and \"user\" = '%s' group by date_trunc('minute', ts))" % u)[0]
    d["out_of_period"] = q("select count(*) from events where year(ts) not in (2018, 2019)")[0]
    d["t3_pairs"] = c.sql("select conflict, count(*) n from ex_T3_pairs group by 1").df().set_index("conflict").n.to_dict()
    d["t3_users"] = q("select count(distinct po_user) from ex_T3")[0]
    d["t3_top_users"] = c.sql("select po_user, count(*) n from ex_T3 group by 1 order by 2 desc limit 5").df().values.tolist()
    d["t3_value_single"] = q("select sum(item_value) from ex_T3")[0]
    return d


if __name__ == "__main__":
    c = connect()
    r = results(c)
    print(r.to_string())
    for t in TESTS:
        c.sql(f"select * from ex_{t}").df().to_parquet(P / f"ex_{t}.parquet")
    r.to_csv(P / "results.csv", index=False)
    import json
    st = stats(c); json.dump(st, open(P / "stats.json", "w"), default=str, indent=1)
    print(st)
