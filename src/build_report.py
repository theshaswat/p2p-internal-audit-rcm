"""Builds outputs/P2P_Internal_Audit_Report.pdf from the test results and the RCM logic."""
import sys
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
sys.path.insert(0, str(Path(__file__).parent))
import rcm_def as D

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "outputs"; PROC = ROOT / "data" / "processed"
ST = D.ST
TODAY = date(2026, 10, 17)
n = lambda v: f"{v:,.0f}"

NAVY = colors.HexColor("#1F3A5F"); GREY = colors.HexColor("#F2F4F7"); LINE = colors.HexColor("#C9D0DA")
RC = {"High": "#FEE4E2", "Medium": "#FEF0C7", "Low": "#D1FADF"}
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=2)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=9, spaceAfter=4, keepWithNext=1)
H3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=NAVY, spaceBefore=6, spaceAfter=2, keepWithNext=1)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9.2, leading=12.6, spaceAfter=3)
SM = ParagraphStyle("sm", parent=B, fontSize=8, leading=10.4, textColor=colors.HexColor("#555555"))
TC = ParagraphStyle("tc", parent=B, fontSize=8.2, leading=10.4, spaceAfter=0)
TH = ParagraphStyle("th", parent=TC, fontName="Helvetica-Bold", textColor=colors.white)
P = lambda t, s=B: Paragraph(t, s)


def table(rows, widths, head=True, shade=None):
    data = [[Paragraph(str(c), TH if (head and i == 0) else TC) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    for (r, c), color in (shade or {}).items(): st.append(("BACKGROUND", (c, r), (c, r), colors.HexColor(color)))
    t.setStyle(TableStyle(st)); return t


# ---------------------------------------------------------------- derive matrix results
M = []
for r in D.ROWS:
    cnt = D.counts(r); tested = cnt is not None
    pop, exc = cnt if tested else (None, None)
    rate = exc / pop if tested else 0
    inh = D.level(r[4] * r[5]); res = D.result(rate, tested)
    M.append(dict(id=r[0], step=r[1], risk=r[2], control=r[7], L=r[4], I=r[5], inh=inh, res=res, resid=D.residual(inh, res),
                  pop=pop, exc=exc, rate=rate, test=r[13], owner=r[11]))
m = {x["id"]: x for x in M}
ex2 = pd.read_parquet(PROC / "ex_T2.parquet"); ex3 = pd.read_parquet(PROC / "ex_T3.parquet")
ex5 = pd.read_parquet(PROC / "ex_T5.parquet")
ex1 = pd.read_parquet(PROC / "ex_T1a.parquet"); gr_rev = (ex1.n_gr_cancel > 0).mean() if len(ex1) else 0
V = {t: float(D.RES.loc[t, "value"]) for t in D.RES.index}
v_r4 = float(ex3[ex3.detail.str.contains("goods receipt")].item_value.sum())
top_v = ex2.groupby("vendor").item_value.sum().sort_values(ascending=False)
top5_share = top_v.head(5).sum() / max(top_v.sum(), 1)
u_top = ST["t3_top_users"][0]; u_share = u_top[1] / max(m["R4"]["exc"] or 1, 1)
due = lambda d: (TODAY + timedelta(days=d)).strftime("%d %b %Y")
pct = lambda r: f"{r:.2%}" if 0 < r < 0.01 else f"{r:.1%}"
rate_s = lambda x: pct(x['rate'])

# ---------------------------------------------------------------- finding text
FIND = {
 "R9": dict(title="Possible duplicate payments", rating_src="R9",
   obs=lambda: f"{n(m['R9']['exc'])} of {n(m['R9']['pop'])} paid items ({rate_s(m['R9'])}, item value {n(V['T2'])}) share vendor, company and value with an item in a different purchase document created within 7 days, and both were paid. Values paid five or more times by one vendor are treated as recurring prices and excluded. The {n(top_v.size)} vendors involved are concentrated: the top five hold {top5_share:.0%} of the value.",
   crit="Each supplier invoice is paid once. A duplicate check on vendor and value runs before every payment run.",
   cause="Probable: the system checks duplicates on invoice number only, so the same order keyed twice under different document numbers passes. Confirm with Accounts Payable.",
   risk="Cash paid twice for one purchase; recovery depends on supplier goodwill.",
   rec="Add vendor, company and value to the pre-payment duplicate check. Review the listed items, recover any confirmed duplicates, and block repeat entries within 7 days without a second approver.",
   act="Run the duplicate review on the listed items and report recoveries; configure the extended check in the payment proposal.", owner="Accounts Payable Manager", days=45),
 "R4": dict(title="Buyers recording goods receipts on their own orders", rating_src="R4",
   obs=lambda: f"{n(m['R4']['exc'])} of {n(m['R4']['pop'])} items ({rate_s(m['R4'])}, item value {n(v_r4)}) were created and goods-received by the same named user. {ST['t3_users']} users are involved; {u_top[0]} alone accounts for {u_share:.0%} of the items. No item had the same person create the order and record or clear its invoice.",
   crit="Creating a purchase order and confirming receipt of the goods are done by different people.",
   cause="Probable: purchasing and receiving roles are combined for some users, possibly in small sites or for services where the buyer confirms delivery. Confirm with IT Security.",
   risk="A buyer can order, receive and so trigger payment for goods that never arrived.",
   rec="Remove the combined access or, where the team is too small to separate, add a monthly review by a manager of every item the buyer both ordered and received. Start with the top users listed in the workbook.",
   act="Run an access review of the listed users; split roles or document a compensating monthly review.", owner="IT Security Manager", days=60),
 "R2": dict(title="Orders that may have been split below the approval limit", rating_src="R2",
   obs=lambda: f"{n(m['R2']['exc'])} items ({rate_s(m['R2'])}, item value {n(V['T5'])}) belong to groups where one buyer raised two or more documents to the same vendor on the same day, each between 4,000 and 10,000 and together at or above 10,000. The approval limit is an assumption because the log holds no approval matrix.",
   crit="Order value, not document count, decides who must approve.",
   cause="Probable: approval is checked per document, so several smaller documents avoid the higher approval level.",
   risk="Spend above a buyer's limit is committed without the approval the policy requires.",
   rec="Aggregate same-vendor, same-day documents when applying approval limits and add a monthly split-order report reviewed by the Procurement Manager. Test the report against the actual approval matrix.",
   act="Build the split-order report and review the listed groups against the approval matrix.", owner="Procurement Manager", days=60),
 "R6": dict(title="Payments made without, or before, a goods receipt", rating_src="R6",
   obs=lambda: f"{m['R6']['exc']} items ({rate_s(m['R6'])}, item value {n(V['T1a'])}) had an invoice cleared with no goods receipt or service entry sheet ever recorded. {gr_rev:.0%} of these had their goods receipt cancelled after the invoice was posted, and the payment was still released. A further {m['R8']['exc']} items ({rate_s(m['R8'])}, item value {n(V['T4'])}) were cleared before their first goods receipt. On the {n(m['R7']['pop'])} items set up for goods-receipt-based verification, {m['R7']['exc']} had an invoice posted ahead of the receipt.",
   crit="An invoice is paid only after the goods or services are received and the invoice matches the order and the receipt.",
   cause="Probable: manual unblocking of invoices held for goods receipt, or receipts recorded outside the system. Confirm with Accounts Payable.",
   risk="Payment for goods or services not received.",
   rec="Review each listed item for evidence of delivery. Restrict manual unblocking of payment blocks to a named person and report every unblocked invoice weekly.",
   act="Obtain proof of delivery for the listed items; restrict and report manual unblocking.", owner="Accounts Payable Manager", days=30),
 "R10": dict(title="Large payment batches run by one user", rating_src="R10",
   obs=lambda: f"{ST['top_clear_user']} cleared {n(ST['top_clear_n'])} of {n(ST['clear_events'])} invoice-clearing events ({ST['top_clear_n']/ST['clear_events']:.0%}), with up to {n(ST['max_clear_minute'])} in a single minute. This shows a payment run executed under one named user. The log does not show whether a second person approved each run.",
   crit="A payment proposal is approved by someone other than the person who runs it.",
   cause="Probable: payment runs are scheduled under a named user's login instead of a controlled batch account. Confirm with the Finance Controller.",
   risk="One credential can release all supplier payments in a run.",
   rec="Run payments from a batch account, keep the proposal approval as a system record, and review the approver against the operator each month.",
   act="Move runs to a batch account and evidence the second approval.", owner="Finance Controller", days=45),
}
ORDER = ["R9", "R4", "R6", "R2", "R10"]
RATE_OF = {"R6": ["R6", "R8", "R7"]}
def finding_rating(key):
    ids = RATE_OF.get(key, [key])
    rs = [m[i]["resid"] for i in ids]
    return "High" if "High" in rs else "Medium" if "Medium" in rs else "Low"
def finding_active(key):
    ids = RATE_OF.get(key, [key])
    if key == "R6":  # three-way match: report whenever exceptions exist, even inside tolerance
        return any(m[i]["exc"] for i in ids)
    return key == "R10" or any(m[i]["res"] in ("Needs improvement", "Ineffective") for i in ids)
VAL = {"R9": V["T2"], "R4": v_r4, "R2": V["T5"], "R6": V["T1a"] + V["T4"], "R10": 0}
acts = [k for k in ORDER if finding_active(k)]
acts.sort(key=lambda k: (["High", "Medium", "Low"].index(finding_rating(k)), -VAL[k]))
nhigh = sum(finding_rating(k) == "High" for k in acts)
opinion = "Unsatisfactory" if nhigh >= 2 else "Needs improvement" if acts else "Satisfactory"

# ---------------------------------------------------------------- document
def foot(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#777777"))
    c.drawString(18 * mm, 10 * mm, "Shaswat Sharma  |  Procure-to-Pay Internal Audit Report")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {d.page}"); c.restoreState()

doc = SimpleDocTemplate(str(OUT / "P2P_Internal_Audit_Report.pdf"), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=17 * mm, title="Procure-to-Pay Internal Audit Report", author="Shaswat Sharma")
f = [P("Procure-to-Pay Internal Audit Report", H1),
     P(f"Report date {TODAY.strftime('%d %B %Y')}  |  Purchase-order process, {ST['cases']:,} items, {ST['docs']:,} purchase documents", SM), Spacer(1, 5)]
f += [table([["Objective", "Test whether the key controls over requisition, ordering, goods receipt, invoicing and payment operated, and report root causes and management actions."],
             ["Data", f"BPI Challenge 2019 event log (4TU.ResearchData, CC BY 4.0): real purchase-order handling at a multinational, {ST['events']:,} events dated 2018 to 2019 ({ST['out_of_period']} carry other dates in the source), {ST['users']} named users. Names, vendors and values are anonymised in the source."],
             ["Approach", "Risk and control matrix built from the process; ten risks mapped to key controls; six SQL tests run over the full population (not a sample); results rated against the key in section 5."],
             ["Overall conclusion", f"<b>{opinion}.</b> {len(acts)} findings need action; {sum(1 for k in acts if finding_rating(k)=='High')} rated High."]],
            [28, 146], head=False), Spacer(1, 6)]

f += [P("1. Summary of findings", H2)]
rows = [["ID", "Finding", "Rating", "Exceptions", "Rate", "Item value"]]; shade = {}
for i, k in enumerate(acts, 1):
    ids = RATE_OF.get(k, [k]); mm_ = m[ids[0]]
    if k == "R6":
        exc = sum(m[j]["exc"] for j in ("R6", "R8", "R7")); pop = "; ".join(str(n(m[j]["pop"])) for j in ("R6", "R8", "R7"))
        rows.append([f"F{i}", FIND[k]["title"], finding_rating(k), n(exc), "see finding", n(V["T1a"] + V["T4"])])
    elif k == "R10":
        rows.append([f"F{i}", FIND[k]["title"], finding_rating(k), "n/a", f"{ST['top_clear_n']/ST['clear_events']:.0%} by one user", "n/a"])
    else:
        val = VAL[k]
        rows.append([f"F{i}", FIND[k]["title"], finding_rating(k), n(mm_["exc"]), rate_s(mm_), n(val)])
    shade[(i, 2)] = RC[finding_rating(k)]
f += [table(rows, [10, 82, 18, 22, 22, 20], shade=shade),
      P("Item value is the purchase-order item value in the log's anonymised units. It shows the amount at stake, not a confirmed loss.", SM)]
cl = [x for x in M if x["res"] == "Effective" and x["exc"] == 0]
if cl:
    f += [P("Controls tested with no exceptions: " + "; ".join(f"{x['id']} {x['risk'].lower()} ({x['exc']} of {n(x['pop'])})" for x in cl) + ".", B)]

f += [P("2. Process reviewed", H2), Image(str(OUT / "process_map.png"), width=172 * mm, height=44.7 * mm),
      PageBreak(), P("3. Risk and control matrix", H2)]
rows = [["ID", "Risk", "Key control", "Inherent", "Test", "Rate", "Conclusion", "Residual"]]; shade = {}
for i, x in enumerate(M, 1):
    rows.append([x["id"], x["risk"], x["control"], x["inh"], x["test"] or "n/a", pct(x["rate"]) if x["pop"] else "n/a", x["res"], x["resid"]])
    shade[(i, 3)] = RC[x["inh"]]; shade[(i, 7)] = RC[x["resid"]]
f += [table(rows, [10, 36, 42, 17, 17, 11, 22, 17], shade=shade),
      P(f"The matrix with owners, frequency, assertions and test procedures is in P2P_Risk_Control_Matrix.xlsx. R1: a requisition event exists for {n(ST['req_items'])} of {n(ST['cases'])} items, so the requisition control cannot be tested from this log. R3: vendor master changes are not in the log.", SM)]

f += [PageBreak(), P("4. Detailed findings", H2)]
for i, k in enumerate(acts, 1):
    t = FIND[k]; r = finding_rating(k)
    blk = [P(f"F{i}  {t['title']}  (Rating: {r}; risk {', '.join(RATE_OF.get(k, [k]))})", H3),
           table([["Observation", t["obs"]()], ["Expected", t["crit"]], ["Probable root cause", t["cause"]], ["Risk", t["risk"]],
                  ["Recommendation", t["rec"]], ["Proposed management action", t["act"]],
                  ["Action owner and due", f"{t['owner']}  |  due {due(t['days'])}"]], [34, 140], head=False), Spacer(1, 4)]
    f += [KeepTogether(blk)]

f += [P("5. Rating key, scope and limits", H2),
      table([["Measure", "Rule"],
             ["Inherent rating", "Likelihood x impact (each 1 to 5): High 15 or more, Medium 8 to 14, Low below 8. Likelihood and impact are reviewer judgement."],
             ["Control conclusion", "Exception rate up to 1% Effective, up to 5% Needs improvement, above 5% Ineffective. No test: Not tested."],
             ["Residual and finding rating", "Effective control lowers the inherent rating one level; otherwise unchanged. A finding takes the highest residual rating of its risks."],
             ["Overall conclusion", "Unsatisfactory if two or more findings are High; Needs improvement if any finding is rated; otherwise Satisfactory."]], [38, 136]),
      Spacer(1, 4),
      P("<b>Limits.</b> The log holds one item value per event, not separate goods receipt and invoice amounts, so three-way match is tested on event sequence and value at risk is the item value. The approval limit in the split-order test and the 7-day window in the duplicate test are reviewer assumptions. Invoice numbers are not in the log, so duplicate hits are leads to verify with source documents. Root causes are inferred from the pattern and must be confirmed with the process owner, and management actions are proposals until accepted.", B)]
doc.build(f, onFirstPage=foot, onLaterPages=foot)
print("report built", opinion, acts)
