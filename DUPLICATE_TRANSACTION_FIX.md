# 重複交易記錄修正

## 問題描述

用戶發現系統顯示了兩筆完全相同的銷帳交易記錄：
- 時間：2025/10/18 下午5:36:46
- 類型：銷帳
- 描述：客戶「小曾」銷帳收款
- 操作人：admin
- TWD 變動：+100,000.00

兩筆記錄的唯一差別是「入款戶餘額變化」中的「前」餘額不同：
- 第一筆：前 63,000.00 → 後 163,000.00
- 第二筆：前 -37,000.00 → 後 63,000.00

## 問題根因

### 1. 雙重記錄創建
當執行銷帳操作時，系統會同時創建兩種記錄：
- **CashLog記錄**：記錄現金日誌（type="SETTLEMENT"）
- **LedgerEntry記錄**：記錄記帳流水（entry_type="SETTLEMENT"）

### 2. 重複處理邏輯
在交易紀錄API中，系統同時處理了這兩種記錄：
- **CashLog處理**（第6570-6616行）：處理現金日誌中的SETTLEMENT記錄
- **LedgerEntry處理**（第6500-6568行）：處理記帳流水中的SETTLEMENT記錄

這導致同一筆銷帳操作在交易紀錄中顯示兩次。

### 3. 餘額計算差異
由於兩筆記錄的處理順序不同，在餘額變化計算時產生了不同的結果：
- 第一筆記錄被計算時，帳戶餘額是63,000.00
- 第二筆記錄被計算時，由於前面已經處理了一筆，所以餘額變成了-37,000.00

## 修正方案

### 1. 排除重複處理
修改LedgerEntry的處理邏輯，排除SETTLEMENT類型的記錄：

**修正前：**
```python
# 處理其他記帳記錄（排除買入相關記錄，但包含銷帳）
for entry in misc_entries:
    if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
```

**修正後：**
```python
# 處理其他記帳記錄（排除買入相關記錄和銷帳，因為銷帳已經在CashLog中處理）
for entry in misc_entries:
    if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT", "SETTLEMENT"]:
```

### 2. 統一處理邏輯
現在銷帳記錄只通過CashLog處理，避免了重複顯示：
- CashLog記錄包含完整的交易信息
- 通過匹配對應的LedgerEntry獲取帳戶信息
- 確保每筆銷帳只顯示一次

## 修正效果

修正後，系統將：
1. **消除重複記錄**：每筆銷帳操作只顯示一次
2. **確保數據一致性**：餘額變化計算基於正確的交易順序
3. **提高數據準確性**：避免因重複處理導致的計算錯誤

## 技術細節

### 數據流程
1. 銷帳操作執行時創建CashLog和LedgerEntry
2. 交易紀錄API只處理CashLog中的SETTLEMENT記錄
3. 通過匹配邏輯從LedgerEntry獲取帳戶信息
4. 確保每筆銷帳在交易紀錄中只出現一次

### 匹配邏輯
```python
# 查找對應的LedgerEntry來獲取帳戶信息
matching_entry = None
for entry in misc_entries:
    if (entry.entry_type == "SETTLEMENT" and 
        entry.description == log.description and
        abs((entry.entry_date - log.time).total_seconds()) < 10):
        matching_entry = entry
        break
```

## 影響範圍

此修正影響：
1. 所有銷帳記錄的顯示
2. 交易紀錄的準確性
3. 帳戶餘額變化的計算

修正後，用戶將看到：
- 每筆銷帳操作只顯示一次
- 正確的帳戶餘額變化信息
- 一致的交易紀錄數據

## 測試建議

1. 執行銷帳操作後，檢查交易紀錄是否只顯示一次
2. 驗證帳戶餘額變化是否正確
3. 確認其他類型的交易記錄不受影響

這個修正解決了重複記錄顯示的問題，提高了系統數據的準確性和一致性。

