# 數據驗證清單

## 請提供以下資料以確保算法正確

### 1️⃣ 帳戶當前餘額（最重要）

請在線上資料庫執行以下查詢，提供這三個帳戶的**當前餘額**：

```sql
SELECT id, name, balance, currency 
FROM cash_accounts 
WHERE id IN (27, 23, 31);
```

**需要提供：**
- 0107支付寶 (ID: 27)：當前餘額 = ?
- 7773支付寶 (ID: 23)：當前餘額 = ?
- 6186支付寶 (ID: 31)：當前餘額 = ?

### 2️⃣ 帳戶交易歷史統計

對於上述三個帳戶，請提供以下統計數據：

```sql
-- 買入/儲值記錄總額（應該增加餘額）
SELECT 
    account_id,
    SUM(CASE WHEN entry_type IN ('DEPOSIT', 'TRANSFER_IN') THEN amount ELSE 0 END) as total_deposits
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
GROUP BY account_id;
```

```sql
-- 售出扣款總額
SELECT 
    account_id,
    SUM(CASE WHEN entry_type = 'WITHDRAW' AND description LIKE '%售出扣款%' THEN ABS(amount) ELSE 0 END) as total_withdrawals
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
GROUP BY account_id;
```

```sql
-- 其他 WITHDRAW 記錄（非售出扣款）
SELECT 
    account_id,
    SUM(CASE WHEN entry_type = 'WITHDRAW' AND description NOT LIKE '%售出扣款%' THEN ABS(amount) ELSE 0 END) as other_withdrawals
FROM ledger_entries
WHERE account_id IN (27, 23, 31)
GROUP BY account_id;
```

### 3️⃣ 銷售記錄統計

```sql
-- 這些帳戶的總銷售金額
SELECT 
    rmb_account_id,
    COUNT(*) as sales_count,
    SUM(rmb_amount) as total_sales
FROM sales_records
WHERE rmb_account_id IN (27, 23, 31)
GROUP BY rmb_account_id;
```

### 4️⃣ 帳戶初始餘額（如果知道）

如果這些帳戶有**初始餘額**或**期初餘額**，請提供：
- 0107支付寶 初始餘額 = ?
- 7773支付寶 初始餘額 = ?
- 6186支付寶 初始餘額 = ?

---

## 根據您提供的資料，我可以：

1. **計算預期餘額**：根據交易記錄計算這些帳戶應該有多少餘額
2. **驗證回補邏輯**：確認回補的金額是否正確
3. **檢測數據錯誤**：發現可能的數據不一致問題
4. **建議清理方案**：基於實際數據決定是否需要回補

---

## 簡化版（最關鍵的資料）

如果您無法提供所有資料，**至少請提供**：

### ✅ 絕對必要
- 帳戶當前餘額（上述三個帳戶）
- 回補後的預期餘額是否正確的**判斷標準**

### ⚠️ 重要
- 您認為這些帳戶**應該**有多少餘額（基於您的業務知識）

---

## 範例查詢腳本

我已經創建了一個完整的驗證腳本，可以提供所有必要信息：

```bash
# 執行驗證腳本
python check_withdraw_verification.py
```

腳本會輸出：
- 當前帳戶餘額
- 所有交易統計
- 預期餘額計算
- 回補建議

