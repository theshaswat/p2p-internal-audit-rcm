"""Risk and control matrix content + the rating logic shared by the workbook and the report."""
import json
from pathlib import Path
import pandas as pd

P = Path(__file__).resolve().parents[1] / "data" / "processed"
RES = pd.read_csv(P / "results.csv").set_index("test")
ST = json.load(open(P / "stats.json"))
pairs = ST["t3_pairs"]
pop3 = int(RES.loc["T3", "population"])
val3 = {}  # value by conflict type filled by caller if needed

NA = None
# (id, step, risk, category, L, I, control id, control, type, nature, freq, owner, assertion, test, procedure)
ROWS = [
 ("R1", "Requisition", "Purchases raised without an approved requisition", "Compliance", 3, 3,
  "C1", "Approved purchase requisition required before a purchase order is raised", "Preventive", "Manual", "Per order", "Procurement Manager",
  "Authorisation", "Coverage", "Count items with a requisition event in the log against all items"),
 ("R2", "Purchase order", "Orders split across documents to stay under the approval limit", "Fraud", 3, 4,
  "C2", "Approval limits enforced by order value; split-order report reviewed monthly", "Preventive + detective", "IT-dependent manual", "Monthly", "Procurement Manager",
  "Authorisation", "T5", "Same buyer, vendor, company and day: 2+ documents, each 4,000 to 10,000, together at or above 10,000"),
 ("R3", "Vendor set-up", "Fictitious or duplicate vendor set up and paid", "Fraud", 2, 5,
  "C3", "Vendor master changes approved by a second person; duplicate vendor check", "Preventive", "IT-dependent manual", "Per change", "Vendor Master Team Lead",
  "Existence", NA, "Not testable: vendor master changes are not in the log"),
 ("R4", "Goods receipt", "Same person orders and receives the goods", "Fraud", 3, 4,
  "C4", "System roles keep purchase order creation and goods receipt with different people", "Preventive", "Automated", "Per transaction", "IT Security Manager",
  "Segregation of duties", "T3a", "Same named user created the item and recorded its goods receipt or service entry sheet"),
 ("R5", "Invoice and payment", "Same person orders and processes the invoice or payment", "Fraud", 2, 5,
  "C5", "System roles keep purchase order creation apart from invoice receipt and payment clearing", "Preventive", "Automated", "Per transaction", "IT Security Manager",
  "Segregation of duties", "T3b", "Same named user created the item and recorded the invoice receipt or cleared the invoice"),
 ("R6", "Three-way match", "Invoice paid for goods or services never received", "Financial", 3, 5,
  "C6", "System blocks payment until a goods receipt is posted (three-way match)", "Preventive", "Automated", "Per invoice", "Accounts Payable Manager",
  "Existence", "T1a", "Items needing a goods receipt with a cleared invoice and no goods receipt or service entry sheet"),
 ("R7", "Three-way match", "Goods-receipt-based invoice verification bypassed", "Financial", 3, 4,
  "C7", "Invoice receipt blocked until goods receipt on items set up for GR-based verification", "Preventive", "Automated", "Per invoice", "Accounts Payable Manager",
  "Accuracy", "T1b", "GR-based items with an invoice receipt posted before the first goods receipt, or with none"),
 ("R8", "Payment", "Supplier paid before the goods are received", "Financial", 3, 4,
  "C8", "Payment released only after the goods receipt date", "Preventive", "Automated", "Per payment run", "Accounts Payable Manager",
  "Cut-off", "T4", "Invoice cleared on a date earlier than the first goods receipt"),
 ("R9", "Payment", "Same supplier paid twice for the same order", "Financial", 3, 5,
  "C9", "Duplicate check on vendor and value before payment; reviewed before each run", "Preventive + detective", "IT-dependent manual", "Per payment run", "Accounts Payable Manager",
  "Occurrence", "T2", "Same vendor, company and value (1,000+), different documents created within 7 days, both paid; recurring prices excluded"),
 ("R10", "Payment run", "One person runs very large payment batches with no independent review", "Operational", 2, 4,
  "C10", "Payment proposal approved by a second person before release", "Preventive", "Manual", "Per payment run", "Finance Controller",
  "Authorisation", "Obs", "Concentration of clearing events by user and the largest single-minute batch"),
]


def counts(r):
    """(population, exceptions) for a matrix row, or None."""
    t = r[13]
    if t in ("T1a", "T1b", "T2", "T4", "T5"):
        return int(RES.loc[t, "population"]), int(RES.loc[t, "exceptions"])
    if t == "T3a":
        return pop3, int(pairs.get("PO + goods receipt", 0))
    if t == "T3b":
        return pop3, int(pairs.get("PO + invoice receipt", 0)) + int(pairs.get("PO + payment clearing", 0))
    return None  # Coverage and Obs are indicators, not exception tests


def level(score):
    return "High" if score >= 15 else "Medium" if score >= 8 else "Low"


def result(rate, tested):
    if not tested:
        return "Not tested"
    return "Effective" if rate <= 0.01 else "Needs improvement" if rate <= 0.05 else "Ineffective"


def residual(inh, res):
    order = ["Low", "Medium", "High"]
    k = order.index(inh)
    if res == "Effective":
        k = max(0, k - 1)
    return order[k]
