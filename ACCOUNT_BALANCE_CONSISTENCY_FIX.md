# 帳戶餘額一致性修正

## 問題描述

用戶發現系統存在嚴重的數據不一致問題：
- **左上角顯示的現金餘額**：163,000（來自資料庫實際餘額）
- **交易紀錄中的現金餘額**：921,680（通過累積計算的虛擬餘額）

這兩個數字相差巨大，說明系統的帳戶餘額計算邏輯存在根本性錯誤。

## 問題根因

### 1. 計算邏輯錯誤
原來的系統在計算交易紀錄中的帳戶餘額變化時，使用了錯誤的計算方式：
- 從最早的交易開始累積計算餘額
- 沒有考慮到實際資料庫餘額與計算餘額的差異
- 導致顯示的餘額與實際餘額不一致

### 2. 數據來源不一致
- **左上角餘額**：直接從 `CashAccount.balance` 讀取
- **交易紀錄餘額**：通過交易記錄累積計算
- 兩種計算方式沒有同步，造成數據不一致

## 修正方案

### 1. 重新設計餘額計算邏輯

**核心原則：以實際資料庫餘額為基準，反向計算歷史餘額**

```python
# 獲取所有帳戶的當前實際餘額
all_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
for account in all_accounts:
    account_balances[account.id] = {
        'name': account.name,
        'currency': account.currency,
        'current_balance': account.balance  # 使用實際資料庫餘額
    }
```

### 2. 計算初始餘額

```python
# 先計算每個帳戶在最早交易前的初始餘額（當前餘額 - 所有交易變動的總和）
for account_id in account_balances:
    total_change = 0
    for record in chronological_stream:
        # 計算所有交易對該帳戶的總變動
        # ...
    
    # 計算初始餘額（當前餘額 - 所有變動）
    account_balances[account_id]['initial_balance'] = account_balances[account_id]['current_balance'] - total_change
```

### 3. 正確計算每筆交易的前後餘額

```python
# 現在從最早記錄開始，正確計算每筆交易的前後餘額
for record in chronological_stream:
    # 計算到這筆交易前的餘額
    for prev_record in chronological_stream:
        if prev_record == record:
            break
        # 累積計算前面所有交易的影響
    
    balance_before = current_balance
    balance_after = balance_before + change
    
    record["account_balance_changes"][account_id] = {
        "account_name": account_info['name'],
        "currency": account_info['currency'],
        "balance_before": balance_before,
        "balance_after": balance_after,
        "change": balance_after - balance_before
    }
```

## 修正效果

修正後，系統將確保：

1. **數據一致性**：交易紀錄中的餘額變化與實際資料庫餘額保持一致
2. **準確性**：每筆交易的前後餘額都是基於實際資料庫狀態計算的
3. **可追溯性**：能夠正確追蹤每個帳戶的餘額變化歷史

## 技術細節

### 計算流程
1. 獲取所有帳戶的當前實際餘額
2. 計算每個帳戶在最早交易前的初始餘額
3. 從最早交易開始，逐筆計算每筆交易的前後餘額
4. 確保最終餘額與實際資料庫餘額一致

### 關鍵改進
- **基準統一**：所有餘額計算都以實際資料庫餘額為基準
- **反向計算**：從當前餘額反推歷史餘額，確保一致性
- **逐筆追蹤**：每筆交易都基於前面所有交易的累積結果

## 影響範圍

此修正影響：
1. 所有交易紀錄的餘額變化顯示
2. 帳戶餘額的一致性驗證
3. 財務報表的準確性

修正後，用戶將看到一致的數據：
- 左上角的帳戶餘額與交易紀錄中的餘額變化保持一致
- 每筆交易的「前」餘額與「後」餘額都是準確的
- 系統提供可信賴的財務追蹤信息

## 測試建議

1. 驗證左上角顯示的餘額與交易紀錄最後一筆的「後」餘額一致
2. 檢查每筆交易的「前」餘額是否等於上一筆交易的「後」餘額
3. 確認所有帳戶的餘額變化計算都是正確的

這個修正解決了系統中最嚴重的數據不一致問題，確保了財務數據的準確性和可靠性。

