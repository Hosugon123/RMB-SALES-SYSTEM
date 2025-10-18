# 銷帳記錄帳戶餘額變化修正

## 問題描述

在交易紀錄中，銷帳記錄（如「客戶「小曾」銷帳收款」）的「入款戶餘額變化」欄位顯示為空的「-」，但應該要顯示具體帳戶（如「007-現金」）的入帳前後餘額變化。

## 問題根因

1. **LedgerEntry排除問題**：在交易紀錄API中，系統錯誤地排除了`SETTLEMENT`類型的LedgerEntry記錄
2. **帳戶ID缺失**：銷帳記錄沒有正確設置`deposit_account_id`，導致無法追蹤具體帳戶的餘額變化
3. **現金日誌處理不完整**：現金日誌中的銷帳記錄雖然找到了對應的LedgerEntry，但沒有正確設置帳戶ID

## 修正內容

### 1. 修正LedgerEntry處理邏輯

**文件：** `app.py` (第6500-6502行)

**修正前：**
```python
# 處理其他記帳記錄（排除銷帳）
for entry in misc_entries:
    if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT", "SETTLEMENT"]:
```

**修正後：**
```python
# 處理其他記帳記錄（排除買入相關記錄，但包含銷帳）
for entry in misc_entries:
    if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
```

### 2. 新增SETTLEMENT類型處理邏輯

**文件：** `app.py` (第6540-6543行)

**新增：**
```python
elif entry.entry_type in ["SETTLEMENT"]:
    # 銷帳：客戶 -> 帳戶
    payment_account = "客戶付款"
    deposit_account = entry.account.name if entry.account else "N/A"
```

### 3. 修正帳戶ID設置邏輯

**文件：** `app.py` (第6555-6556行)

**修正前：**
```python
"deposit_account_id": entry.account.id if entry.account and entry.entry_type in ["DEPOSIT", "TRANSFER_IN"] else None,
```

**修正後：**
```python
"deposit_account_id": entry.account.id if entry.account and entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"] else None,
```

### 4. 修正現金日誌銷帳記錄處理

**文件：** `app.py` (第6576-6595行)

**修正：**
```python
elif log.type == "SETTLEMENT":
    twd_change = log.amount
    payment_account = "客戶付款"
    deposit_account = "N/A"
    deposit_account_id = None
    
    # 查找對應的LedgerEntry來獲取帳戶信息
    matching_entry = None
    for entry in misc_entries:
        if (entry.entry_type == "SETTLEMENT" and 
            entry.description == log.description and
            abs((entry.entry_date - log.time).total_seconds()) < 10):
            matching_entry = entry
            break
    
    if matching_entry and matching_entry.account:
        deposit_account = matching_entry.account.name
        deposit_account_id = matching_entry.account.id
    else:
        deposit_account = "現金帳戶"
```

### 5. 更新unified_stream添加邏輯

**文件：** `app.py` (第6610行)

**修正：**
```python
"deposit_account_id": deposit_account_id if 'deposit_account_id' in locals() else None,
```

## 修正效果

修正後，銷帳記錄將正確顯示：

### 交易記錄示例
- **時間：** 2025/10/18 下午5:36:46
- **類型：** 銷帳
- **描述：** 客戶「小曾」銷帳收款
- **操作人：** admin
- **出款戶：** 客戶付款
- **入款戶：** 現金
- **TWD 變動：** +100,000.00
- **入款戶餘額變化：** 
  ```
  007-現金
  前: 63,000.00
  變動: +100,000.00
  後: 163,000.00
  ```

## 技術細節

### 數據流程
1. 客戶銷帳時，系統創建LedgerEntry記錄（entry_type="SETTLEMENT"）
2. 同時創建CashLog記錄（type="SETTLEMENT"）
3. 交易紀錄API現在會處理這兩種記錄類型
4. 正確設置deposit_account_id，指向具體的現金帳戶
5. 帳戶餘額變化追蹤系統能夠計算該帳戶的餘額變化

### 帳戶餘額變化計算
```python
# 從最早的記錄開始計算每個帳戶的餘額變化
chronological_stream = sorted(unified_stream, key=lambda x: x["date"])

for record in chronological_stream:
    # 記錄出帳前餘額
    if deposit_account_id and deposit_account_id in account_balances:
        account_info = account_balances[deposit_account_id]
        record["account_balance_changes"][deposit_account_id] = {
            "account_name": account_info['name'],
            "currency": account_info['currency'],
            "balance_before": account_info['current_balance'],
            "balance_after": account_info['current_balance'],
            "change": 0
        }
    
    # 計算變動並更新帳戶餘額
    # 更新入款帳戶餘額
    if deposit_account_id and deposit_account_id in account_balances:
        account_info = account_balances[deposit_account_id]
        if account_info['currency'] == 'TWD':
            account_info['current_balance'] += twd_change
            record["account_balance_changes"][deposit_account_id]["change"] = twd_change
        record["account_balance_changes"][deposit_account_id]["balance_after"] = account_info['current_balance']
```

## 測試

創建了測試頁面 `test_settlement_account_balance.html` 來驗證修正效果，包含：
- 模擬銷帳記錄數據
- 預期結果說明
- 完整的帳戶餘額變化顯示

## 影響範圍

此修正影響：
1. 所有銷帳記錄的顯示
2. 現金帳戶餘額變化的追蹤
3. 交易紀錄的完整性

修正後，用戶能夠清楚看到每筆銷帳對具體現金帳戶的影響，提供更詳細的財務追蹤信息。

