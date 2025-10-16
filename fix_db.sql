-- 修復數據庫結構 - 添加利潤詳細欄位
ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT;
ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT;
ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT;


