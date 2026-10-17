-- T5 split orders: one person raises 2+ items in different documents, same vendor, company and day.
-- Each item is between 4,000 and 10,000 (just under the illustrative approval limit of 10,000) but
-- together they reach the limit. The log holds no approval matrix; the limit is an assumption set at
-- about the 90th percentile of item value, on the log's anonymised scale.
create or replace table pop_T5 as
select count(*) as n from item_facts
where po_user like 'user\_%' escape '\' and item_value < 10000;

create or replace table ex_T5 as
with g as (
  select po_user, vendor, company, cast(po_ts as date) as d,
         count(*) as n_items, count(distinct doc) as n_docs, sum(item_value) as total
  from item_facts
  where po_user like 'user\_%' escape '\' and item_value >= 4000 and item_value < 10000
  group by all
  having count(distinct doc) >= 2 and sum(item_value) >= 10000)
select f.case_id, f.doc, f.vendor, f.company, f.item_value, f.po_user,
       'Day total ' || cast(round(g.total) as bigint) || ' across ' || g.n_docs || ' documents' as detail
from item_facts f join g
  on f.po_user = g.po_user and f.vendor = g.vendor and f.company = g.company and cast(f.po_ts as date) = g.d
where f.item_value >= 4000 and f.item_value < 10000;
