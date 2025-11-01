# 歷史售出扣款 WITHDRAW 記錄清理指南

## 問題描述

過去的售出流程會創建 WITHDRAW LedgerEntry 記錄（描述為"售出扣款"），這些記錄現在是多餘的，因為：

1. **重複顯示**：售出記錄已經在流水頁面顯示了完整的扣款信息，不需要額外的 WITHDRAW 記錄
2. **顯示混亂**：用戶在流水頁面會看到兩條記錄：
   - 一條 "售出扣款" WITHDRAW 記錄
   - 一條 "售出" 記錄
   兩條記錄都顯示扣款，造成混淆
3. **餘額計算錯誤**：如果 WITHDRAW 記錄使用負數 amount，顯示邏輯可能出錯

## 修復方案

### 1. 移除創建重複 WITHDRAW 記錄的代碼

已修復 `app.py` 中的 `FIFOService.allocate_inventory_for_sale` 方法：

```python
# 修復前（錯誤）：
# 創建 LedgerEntry 記錄餘額變動（金額為負數表示出款）
ledger_entry = LedgerEntry(
    entry_type="WITHDRAW",
    account_id=deduction_account.id,
    amount=-rmb_amount,
    description=f"售出扣款：客戶 {sales_record.customer.name if sales_record.customer else 'N/A'}，銷售記錄 ID {sales_record.id}",
    operator_id=get_safe_operator_id()
)
db.session.add(ledger_entry)

# 修復後（正確）：
# 注意：不創建 WITHDRAW LedgerEntry，因為售出記錄已經會在流水頁面顯示完整的扣款信息
# 避免重複顯示造成混淆
```

### 2. 修復 WITHDRAW 顯示邏輯的餘額計算錯誤

修復了 `app.py` 中兩個 API 的餘額計算邏輯：

#### 完整版 API (`/api/cash_management/transactions`)
- 位置：第 9349-9359 行
- 問題：WITHDRAW 可能使用負數 amount，但計算餘額時假設為正數
- 修復：使用 `abs(entry.amount)` 確保正確計算

#### 簡化版 API (`/api/cash_management/transactions_simple`)
- 位置：第 9869-9875 行（顯示邏輯）和第 9949-9959 行（餘額計算）
- 問題：同完整版 API
- 修復：使用 `-abs(entry.amount)` 確保正確顯示和計算

### 3. 新增清理命令

已新增 Flask CLI 命令來清理歷史數據：

#### 命令：`flask cleanup-sales-withdraw`

```bash
# 執行清理命令
flask cleanup-sales-withdraw
```

**功能：**
1. 查詢所有描述包含"售出扣款"的 WITHDRAW LedgerEntry 記錄
2. 按帳戶統計記錄數量和總扣款金額
3. 回補所有帳戶的餘額（將被錯誤扣除的金額加回去）
4. 刪除所有重複的 WITHDRAW 記錄
5. 顯示清理結果

**使用方式：**
```bash
# 在項目根目錄執行
flask cleanup-sales-withdraw
```

**注意事項：**
- ⚠️  此命令會修改資料庫，建議先備份
- ⚠️  命令會要求確認後才執行
- ✅ 清理前會顯示詳細統計資訊
- ✅ 如果沒有需要清理的記錄，會直接退出

**輸出示例：**
```
🔍 開始分析歷史售出扣款 WITHDRAW 記錄...

找到 4 筆售出扣款 WITHDRAW 記錄

統計資訊：
--------------------------------------------------------------------------------
帳戶: 測試用 (ID: 1)
  記錄數量: 4 筆
  總扣款金額: 7620.00 RMB
--------------------------------------------------------------------------------
總記錄數: 4 筆
總扣款金額: 7620.00 RMB

⚠️  警告：此操作會刪除 LedgerEntry 記錄並調整帳戶餘額！
是否繼續？(yes/no): yes

✅ 帳戶 測試用: 回補 7620.00 RMB
   餘額變化: -380.00 -> 7240.00

✅ 清理完成！
   刪除記錄: 4 筆
   回補餘額: 7620.00 RMB
```

## 修復效果

### 修復前：
- 流水頁面顯示兩條記錄：WITHDRAW "售出扣款" 和 "售出"
- 餘額變化可能顯示錯誤（如 +1000 而不是 -1000）
- 用戶混淆，無法確定實際扣款金額

### 修復後：
- 流水頁面只顯示一條 "售出" 記錄
- 餘額變化正確顯示為負數（扣款）
- 顯示清晰，邏輯一致

## 相關文件

- `app.py`：核心修復代碼
- `fix_withdraw_sales_deduction.py`：獨立腳本（提供更多控制選項）

## 後續維護

未來如果有其他類似的 WITHDRAW 記錄需要清理，可以使用相同的命令模式：

1. 查詢特定模式的 LedgerEntry
2. 統計影響範圍
3. 回補帳戶餘額（如果需要）
4. 刪除重複記錄

## 聯繫

如有問題，請參考代碼註釋或聯繫開發團隊。

