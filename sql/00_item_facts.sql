-- One row per purchase item (case): who created it, receipt/invoice/payment milestones, item value.
-- Net receipts = recorded minus cancelled. Goods receipt equivalent = Record Goods Receipt, or Record Service Entry Sheet for service items.
create or replace table item_facts as
select
  e.case_id,
  any_value(c."Purchasing Document") as doc,
  any_value(c.Vendor) as vendor,
  any_value(c.Company) as company,
  any_value(c."Item Type") as item_type,
  any_value(c."Item Category") as item_cat,
  any_value(c."Goods Receipt" = 'true') as gr_required,
  any_value(c."GR-Based Inv. Verif." = 'true') as gr_based_iv,
  arg_min(e."user", e.ts) filter (where e.activity = 'Create Purchase Order Item') as po_user,
  min(e.ts) filter (where e.activity = 'Create Purchase Order Item') as po_ts,
  arg_min(e.net_worth, e.ts) filter (where e.activity = 'Create Purchase Order Item') as item_value,
  min(e.ts) filter (where e.activity in ('Record Goods Receipt', 'Record Service Entry Sheet')) as first_gr_ts,
  count(*) filter (where e.activity in ('Record Goods Receipt', 'Record Service Entry Sheet')) as n_gr,
  min(e.ts) filter (where e.activity = 'Record Invoice Receipt') as first_ir_ts,
  count(*) filter (where e.activity = 'Record Invoice Receipt') as n_ir,
  count(*) filter (where e.activity = 'Cancel Invoice Receipt') as n_ir_cancel,
  count(*) filter (where e.activity = 'Cancel Goods Receipt') as n_gr_cancel,
  min(e.ts) filter (where e.activity = 'Clear Invoice') as first_clear_ts,
  count(*) filter (where e.activity = 'Clear Invoice') as n_clear
from events e join cases c using (case_id)
group by e.case_id;
