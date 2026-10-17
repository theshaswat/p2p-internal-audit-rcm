# Procure-to-Pay Internal Audit: Risk and Control Matrix

An internal-audit style review of the purchase-to-pay process using a real purchase-order event log (BPI Challenge 2019, a multinational's order handling). Ten risks are mapped to key controls in a risk and control matrix, six SQL tests run over the whole population, and the results are written up as an audit report with root causes and management actions.

## Result

251,734 purchase items, 76,349 purchase documents, 1,595,923 events, 607 named users. Overall conclusion: **Needs improvement**, five findings, one rated High.

| Test | Risk | Population | Exceptions | Rate | Control conclusion |
|---|---|---|---|---|---|
| T2 Same vendor, company and value in a different document within 7 days, both paid | Duplicate payment | 70,817 | 2,175 | 3.1% | Needs improvement (High) |
| T3 Same user created the order and recorded the goods receipt | Segregation of duties | 217,772 | 5,149 | 2.4% | Needs improvement |
| T5 Same buyer, vendor and day: 2+ documents between 4,000 and 10,000, total at or above 10,000 | Split orders | 214,059 | 5,511 | 2.6% | Needs improvement |
| T1a Invoice cleared with no net goods receipt (reversals excluded) | Three-way match | 181,833 | 109 | 0.06% | Effective |
| T4 Invoice cleared before the first goods receipt | Payment timing | 181,777 | 87 | 0.05% | Effective |
| T1b Invoice posted before goods receipt on GR-based items | Three-way match | 11,128 | 0 | 0% | Effective |

Also found: one named user cleared 86% of all invoice-clearing events, up to 4,038 in a single minute.

## Files

| File | What it is |
|---|---|
| `outputs/P2P_Internal_Audit_Report.pdf` | Findings with observation, expected, root cause, risk, recommendation, management action, owner and due date; rating key and limits |
| `outputs/P2P_Risk_Control_Matrix.xlsx` | The matrix (live formulas for scores, rates, conclusions, residual risk), test results, top 300 exceptions per test |
| `sql/` | One DuckDB SQL file per test, plus the item-level fact table |
| `src/` | `parse_xes.py`, `run_tests.py`, `check.py`, `build_rcm.py`, `build_report.py` |

## Run it

The log is on 4TU.ResearchData (doi 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1). Save it as `data/raw/BPI_Challenge_2019.xes`, then:

```
pip install -r requirements.txt
python src/parse_xes.py && python src/run_tests.py && python src/check.py
python src/build_rcm.py && python src/build_report.py
```

`check.py` confirms the parsed log matches the published totals and that every exception table ties to the results.

## Limits

- The log holds one item value per event, not separate goods receipt and invoice amounts. Three-way match is tested on event sequence; value at risk is the item value. Values are anonymised in the source.
- No vendor master changes, approval matrix or invoice numbers. The vendor-set-up risk is documented but not tested. The 10,000 approval limit and the 7-day duplicate window are my assumptions.
- Duplicate-payment hits are leads to check against invoices, not confirmed duplicates. Root causes are inferred from the pattern and need confirming with the process owner; management actions are proposals.

## Data

BPI Challenge 2019, Boudewijn van Dongen, 4TU.ResearchData, CC BY 4.0.
