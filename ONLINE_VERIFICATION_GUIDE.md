# 線上資料庫驗證指南

## 如何在線上資料庫使用驗證腳本

### 方法1：使用 Flask CLI 命令（最簡單）

在線上環境執行：

```bash
# 直接連接到線上資料庫（DATABASE_URL 已設置）
python check_withdraw_verification.py
```

這會自動使用線上資料庫進行驗證。

### 方法2：設置環境變數

```bash
export USE_ONLINE_DB=true
python check_withdraw_verification.py
```

### 方法3：手動提供數據（如果不方便連接）

請在線上資料庫執行以下 SQL 查詢，並提供結果：

## 必要查詢

### 查詢1：帳戶當前餘額

```sql
SELECT id, name, balance, currency 
FROM cash_accounts 
WHERE id IN (27, 23, 31);
```

**請提供結果：**
```
id | name       | balance  | currency
27 | 0107支付寶 | ?        | RMB
23 | 7773支付寶 | ?        | RMB
31 | 6186支付寶 | ?        | RMB
```

### 查詢2：買入/儲值總額

```sql
SELECT 
    account_id,
    SUM(CASE WHEN entry_type IN ('DEPOSIT', 'TRANSFER_IN') THEN amount ELSE 0 END) as total_deposits
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
GROUP BY account_id
ORDER BY account_id;
```

### 查詢3：這些帳戶的總銷售金額

```sql
SELECT 
    rmb_account_id as account_id,
    COUNT(*) as sales_count,
    SUM(rmb_amount) as total_sales
FROM sales_records
WHERE rmb_account_id IN (27, 23, 31)
GROUP BY rmb_account_id
ORDER BY rmb_account_id;
```

### 查詢4：其他 WITHDRAW（非售出扣款）

```sql
SELECT 
    account_id,
    COUNT(*) as count,
    SUM(ABS(amount)) as total_withdraw
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
  AND entry_type = 'WITHDRAW'
  AND description NOT LIKE '%售出扣款%'
GROUP BY account_id
ORDER BY account_id;
```

### 查詢5：售出扣款 WITHDRAW 明細

```sql
SELECT 
    account_id,
    COUNT(*) as count,
    SUM(ABS(amount)) as total_withdraw,
    MIN(entry_date) as earliest,
    MAX(entry_date) as latest
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
  AND entry_type = 'WITHDRAW'
  AND description LIKE '%售出扣款%'
GROUP BY account_id
ORDER BY account_id;
```

---

## 提供數據後，我會幫您：

1. ✅ 計算每個帳戶的**預期餘額**
2. ✅ 判斷當前餘額是否**正確**
3. ✅ 確定是否需要**回補**
4. ✅ 給出**具體的清理建議**

---

## 最簡化版本（如果您只想確認一個數字）

如果您只想快速確認，請提供：

### 只需這兩個查詢

**查詢A：帳戶餘額**
```sql
SELECT id, name, balance FROM cash_accounts WHERE id IN (27, 23, 31);
```

**查詢B：這些帳戶是否有未結清的銷售記錄**
```sql
SELECT 
    rmb_account_id,
    COUNT(*) as count,
    SUM(rmb_amount) as total
FROM sales_records
WHERE rmb_account_id IN (27, 23, 31) 
  AND is_settled = FALSE
GROUP BY rmb_account_id;
```

如果能提供這兩個結果，我可以給出基本判斷。

---

## 您可以用這個模板回覆

```
帳戶餘額：
- 0107支付寶 (ID: 27): X RMB
- 7773支付寶 (ID: 23): X RMB
- 6186支付寶 (ID: 31): X RMB

買入總額：
- 0107支付寶: X RMB
- 7773支付寶: X RMB
- 6186支付寶: X RMB

銷售總額：
- 0107支付寶: X RMB
- 7773支付寶: X RMB
- 6186支付寶: X RMB

其他資訊：[如果有其他重要資訊，請補充]
```

