# 歷史 SalesRecord LedgerEntry 修正指南

## 🎯 問題說明

本次修正包含兩個部分：

### 1. 前瞻性修正（已完成）
在 `FIFOService.allocate_inventory_for_sale` 中添加了 LedgerEntry 創建邏輯，確保**新創建的 SalesRecord** 會自動記錄 RMB 帳戶餘額變動（變動值為負數）。

**位置**：`app.py` 第963-986行

### 2. 歷史數據修正（需手動執行腳本）
對於**已經存在的歷史 SalesRecord**，本修正**不會自動修正**它們，因為：
- 歷史餘額可能已經被其他操作影響
- 需要謹慎處理以避免數據不一致
- 需要人工確認每個修正

## 🔧 如何修正歷史數據

### 步驟 1：執行修正腳本

```bash
python fix_historical_sales_ledger_entries.py
```

### 步驟 2：確認修正

腳本會：
1. 檢查所有歷史 SalesRecord
2. 找出缺少 LedgerEntry 的記錄
3. 根據 FIFOSalesAllocation 創建缺失的 LedgerEntry
4. 驗證帳戶餘額是否正確

### 步驟 3：檢查輸出

腳本會顯示：
- 發現多少筆記錄缺少 LedgerEntry
- 為哪些帳戶創建了 LedgerEntry
- 帳戶餘額驗證報告

## ⚠️ 注意事項

1. **備份資料庫**：執行前請先備份資料庫！
2. **測試環境**：建議先在測試環境執行
3. **停止服務**：執行時建議停止應用服務
4. **檢查結果**：執行後請仔細檢查輸出報告

## 📋 腳本功能說明

### 檢查邏輯
1. 遍歷所有 SalesRecord
2. 對每個 SalesRecord，根據 FIFOSalesAllocation 確定應該扣款的帳戶
3. 檢查是否已經存在對應的 LedgerEntry（在銷售時間前後5分鐘內）
4. 如果不存在，標記為需要修正

### 修正邏輯
1. 為缺失的 LedgerEntry 創建記錄
2. 使用正確的：
   - `entry_type`: "WITHDRAW"
   - `amount`: 負數（表示出款）
   - `account_id`: 扣款帳戶
   - `entry_date`: 原銷售記錄的時間
   - `description`: 包含庫存批次 ID

### 驗證邏輯
1. 重新計算每個帳戶的餘額（從 LedgerEntry）
2. 與實際餘額比較
3. 如果差異超過 0.01，發出警告

## 🎉 修正完成後的狀態

修正完成後：
- ✅ 所有歷史 SalesRecord 都有對應的 LedgerEntry
- ✅ LedgerEntry 的變動值為負數（major 出款）
- ✅ 帳戶餘額計算正確
- ✅ 新創建的 SalesRecord 自動包含 LedgerEntry

## 📞 如有問題

如果執行中遇到問題：
1. 檢查資料庫連接
2. 確認 FIFOSalesAllocation 數據完整
3. 查看腳本輸出的詳細錯誤訊息
4. 檢查資料庫備份是否可用

