# 售出扣款 WITHDRAW 記錄清理詳細說明

## 問題核心

### 過去的扣款流程（產生重複扣款）

**步驟1：FIFOService.allocate_inventory_for_sale (990-993行)**
```python
# 直接從帳戶扣款
deduction_account.balance -= rmb_amount
```

**步驟2：創建 WITHDRAW LedgerEntry (舊代碼，已移除)**
```python
ledger_entry = LedgerEntry(
    entry_type="WITHDRAW",
    account_id=deduction_account.id,
    amount=-rmb_amount,
    description=f"售出扣款：客戶..."
)
```

### 問題

同一次售出操作造成**雙重扣款**：
1. **FIFO 扣款**：從 `deduction_account.balance` 直接扣減
2. **WITHDRAW 記錄**：只是顯示記錄，但由於存在 LedgerEntry，流水頁面會再次顯示扣款

用戶看到兩條記錄都顯示扣款，造成混淆。

## 修復後的流程

**步驟1：FIFOService.allocate_inventory_for_sale (990-998行)**
```python
# 直接從帳戶扣款
deduction_account.balance -= rmb_amount

# 不創建 WITHDRAW LedgerEntry，因為售出記錄已經會在流水頁面顯示完整的扣款信息
# 避免重複顯示造成混淆
```

**結果：**
- ✅ 帳戶只被扣款一次
- ✅ 流水頁面只顯示一條 "售出" 記錄

## 清理歷史數據的正確性

### 為什麼需要回補餘額？

**過去的錯誤流程：**
```
售出 1000 RMB
↓
1. FIFO 扣款：帳戶餘額 -1000 ✓ (正確)
2. 創建 WITHDRAW：LedgerEntry 記錄 -1000 (多餘)
```

**清理歷史記錄時：**
- 帳戶當前餘額已經是：被雙重影響後的餘額
- 如果我們只是刪除 WITHDRAW 記錄，帳戶餘額不會自動調整
- 所以需要手動回補被錯誤影響的金額

### 清理腳本的邏輯

```python
# 1. 計算每個帳戶被 WITHDRAW 記錄影響的總額
for record in withdraw_records:
    account_stats[account_id]['total_amount'] += abs(record.amount)

# 2. 回補帳戶餘額
account.balance += stats['total_amount']  # 加回去

# 3. 刪除 WITHDRAW 記錄
db.session.delete(record)
```

### 清理結果驗證

從清理日誌可以看到：
```
帳戶 123: 回補 2620.00 RMB
  餘額變化: 16000.00 -> 18620.00  ✓ (正確)

帳戶 123: 回補 7690.00 RMB
  餘額變化: -380.00 -> 7310.00  ✓ (正確)

帳戶 測試用: 回補 7000.00 RMB
  餘額變化: 42000.00 -> 49000.00  ✓ (正確)
```

## 總結

**修復包含兩個部分：**

### 1. 代碼修復（防止未來問題）
- ✅ 移除創建重複 WITHDRAW LedgerEntry 的代碼
- ✅ 修復顯示邏輯的餘額計算錯誤
- ✅ 統一 WITHDRAW 處理邏輯

### 2. 數據修復（清理歷史錯誤）
- ✅ 回補帳戶餘額（抵消重複扣款的影響）
- ✅ 刪除重複的 WITHDRAW LedgerEntry 記錄
- ✅ 驗證清理結果（0 筆剩餘記錄）

**修復後的結果：**
- ✅ 帳戶餘額正確
- ✅ 流水顯示清晰（只有一條售出記錄）
- ✅ 餘額變化正確（-1000 而不是 +1000）
- ✅ 未來不再產生重複記錄

