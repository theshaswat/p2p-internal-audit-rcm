-- T1b three-way match: item set up for goods-receipt-based invoice verification, yet an invoice
-- receipt was posted before the goods receipt (or with none). The system block was bypassed.
create or replace table pop_T1b as
select count(*) as n from item_facts
where gr_based_iv and gr_required and item_type <> 'Consignment' and n_ir > 0;

create or replace table ex_T1b as
select case_id, doc, vendor, company, item_value, first_ir_ts, first_gr_ts,
       'GR-based invoice receipt posted before goods receipt' as detail
from item_facts
where gr_based_iv and gr_required and item_type <> 'Consignment' and n_ir > 0
  and (n_gr = 0 or first_ir_ts < first_gr_ts);
