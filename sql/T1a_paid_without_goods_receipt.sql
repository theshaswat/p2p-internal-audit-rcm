-- T1a three-way match: an invoice receipt still stands (recorded and not cancelled) and the invoice was
-- cleared, yet the item has no net goods receipt (none recorded, or all cancelled).
-- Items whose invoice receipts were all cancelled are reversals and are left out.
create or replace table pop_T1a as
select count(*) as n from item_facts
where gr_required and item_type <> 'Consignment' and n_clear > 0 and n_ir > n_ir_cancel;

create or replace table ex_T1a as
select case_id, doc, vendor, company, item_value, n_clear, n_gr, n_gr_cancel,
       'Invoice cleared, no goods receipt or service entry sheet on the item' as detail
from item_facts
where gr_required and item_type <> 'Consignment' and n_clear > 0 and n_ir > n_ir_cancel
  and n_gr - n_gr_cancel <= 0;
