# 🛠️ 利潤詳細記錄數據庫修復指南

## 問題描述

**錯誤信息：**
```
(sqlite3.OperationalError) no such column: ledger_entries.profit_before
```

**原因：** 我們修改了 LedgerEntry 模型，添加了新的利潤詳細欄位，但數據庫還沒有更新。

## 解決方案

### 方案 1：手動添加數據庫欄位（推薦）

1. **停止應用程序**

2. **執行以下 SQL 命令**：
   ```sql
   ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT;
   ```

3. **重新啟動應用程序**

### 方案 2：使用 Python 腳本修復

1. **創建修復腳本** `fix_db.py`：
   ```python
   import sqlite3
   
   conn = sqlite3.connect('instance/sales_system.db')
   cursor = conn.cursor()
   
   try:
       cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT')
       print('Added profit_before')
   except:
       print('profit_before exists')
   
   try:
       cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT')
       print('Added profit_after')
   except:
       print('profit_after exists')
   
   try:
       cursor.execute('ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT')
       print('Added profit_change')
   except:
       print('profit_change exists')
   
   conn.commit()
   conn.close()
   print('Database fixed!')
   ```

2. **執行腳本**：
   ```bash
   python fix_db.py
   ```

### 方案 3：使用數據庫管理工具

1. **打開數據庫管理工具**（如 DB Browser for SQLite）

2. **打開數據庫文件**：`instance/sales_system.db`

3. **執行 SQL**：
   ```sql
   ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT;
   ```

4. **保存更改**

## 臨時解決方案

如果您需要立即使用應用程序，我已經修改了代碼，使其能夠優雅地處理缺失的欄位：

- 使用 `getattr(entry, 'profit_before', None)` 安全地獲取欄位值
- 使用 `hasattr(entry, 'profit_before')` 檢查欄位是否存在
- 如果欄位不存在，會顯示 "-" 而不是報錯

## 驗證修復

修復後，您可以：

1. **重新啟動應用程序**
2. **訪問現金管理頁面**
3. **進行利潤提款測試**
4. **檢查近期交易記錄** - 應該看到新的利潤詳細欄位

## 預期結果

修復後，利潤提款記錄將顯示：

| 變動前利潤 | 變動後利潤 | 變動之利潤數字 |
|------------|------------|----------------|
| 24,431.00  | 23,931.00  | -500.00        |

## 注意事項

- 修復數據庫後，新的利潤提款記錄會包含詳細信息
- 舊的記錄可能沒有詳細信息，會顯示 "-"
- 這是正常的，因為舊記錄是在添加欄位之前創建的
