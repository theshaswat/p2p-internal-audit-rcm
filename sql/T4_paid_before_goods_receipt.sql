-- T4 payment timing: invoice cleared before the first goods receipt on an item that needs one,
-- where an invoice receipt still stands (recorded and not cancelled).
create or replace table pop_T4 as
select count(*) as n from item_facts
where gr_required and item_type <> 'Consignment' and n_clear > 0 and n_gr > 0 and n_ir > n_ir_cancel;

create or replace table ex_T4 as
select case_id, doc, vendor, company, item_value, first_clear_ts, first_gr_ts,
       'Invoice cleared ' || datediff('day', first_clear_ts, first_gr_ts) || ' days before first goods receipt' as detail
from item_facts
where gr_required and item_type <> 'Consignment' and n_clear > 0 and n_gr > 0 and n_ir > n_ir_cancel
  and first_clear_ts < first_gr_ts;
