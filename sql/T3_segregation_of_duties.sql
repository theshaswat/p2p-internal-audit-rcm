-- T3 segregation of duties: one named person (batch and unrecorded users excluded) both created
-- the purchase order item and recorded the receipt, the invoice, or the payment clearing on it.
create or replace table pop_T3 as
select count(*) as n from item_facts
where po_user like 'user\_%' escape '\' and (n_gr > 0 or n_ir > 0 or n_clear > 0);

create or replace table ex_T3_pairs as
select distinct f.case_id,
  case when e.activity in ('Record Goods Receipt', 'Record Service Entry Sheet') then 'PO + goods receipt'
       when e.activity = 'Record Invoice Receipt' then 'PO + invoice receipt'
       else 'PO + payment clearing' end as conflict
from item_facts f
join events e on e.case_id = f.case_id and e."user" = f.po_user
where f.po_user like 'user\_%' escape '\'
  and e.activity in ('Record Goods Receipt', 'Record Service Entry Sheet', 'Record Invoice Receipt', 'Clear Invoice');

create or replace table ex_T3 as
select f.case_id, f.doc, f.vendor, f.company, f.item_value, f.po_user,
       string_agg(p.conflict, '; ' order by p.conflict) as detail
from ex_T3_pairs p join item_facts f using (case_id)
group by f.case_id, f.doc, f.vendor, f.company, f.item_value, f.po_user;
