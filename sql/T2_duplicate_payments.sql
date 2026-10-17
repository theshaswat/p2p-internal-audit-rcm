-- T2 duplicate payments: same vendor and company, same item value (>= 1,000), different purchasing
-- documents created within 7 days of each other, and both invoices cleared. Payment runs clear
-- hundreds of invoices in one minute, so clearing date is not used as the match key.
-- Vendor/value combinations paid 5 or more times are treated as recurring or contract pricing and
-- left out. The later-created item is flagged. Invoice numbers are not in the log, so hits are leads to verify.
create or replace table pop_T2 as
select count(*) as n from item_facts where n_clear > 0 and item_value >= 1000;

create or replace table ex_T2 as
with c as (
  select case_id, doc, vendor, company, item_value, po_ts
  from (select *, count(*) over (partition by vendor, company, item_value) as same_n
        from item_facts where n_clear > 0 and item_value >= 1000)
  where same_n < 5)
select a.case_id, a.doc, a.vendor, a.company, a.item_value,
       min(b.case_id) as matched_item, a.po_ts,
       'Same vendor and value as an item in another document created within 7 days; both paid' as detail
from c a join c b
  on a.vendor = b.vendor and a.company = b.company and a.item_value = b.item_value and a.doc <> b.doc
 and (b.po_ts < a.po_ts or (b.po_ts = a.po_ts and b.case_id < a.case_id))
 and a.po_ts - b.po_ts <= interval 7 day
group by a.case_id, a.doc, a.vendor, a.company, a.item_value, a.po_ts;
