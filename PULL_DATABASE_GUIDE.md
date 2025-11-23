# 資料庫下拉指南

## 📥 功能說明

此工具可以將部署端（Render PostgreSQL）的資料庫完整下拉到本地 SQLite 資料庫，方便進行精確測試。

## 🚀 使用方法

### 方法 1：直接執行（推薦）

```bash
python pull_deployment_db.py
```

腳本會自動：
1. 檢查環境變數 `DATABASE_URL`
2. 如果沒有，會提示您輸入部署端資料庫連接字串
3. 備份本地資料庫
4. 從部署端讀取所有資料
5. 清空本地資料庫
6. 將資料寫入本地 SQLite

### 方法 2：設置環境變數後執行

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="postgresql+psycopg://rmb_user:YOUR_PASSWORD@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
python pull_deployment_db.py
```

**Windows CMD:**
```cmd
set DATABASE_URL=postgresql+psycopg://rmb_user:YOUR_PASSWORD@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4
python pull_deployment_db.py
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql+psycopg://rmb_user:YOUR_PASSWORD@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
python pull_deployment_db.py
```

## 📋 同步的資料表

腳本會同步以下所有資料表：

### 基礎表
- `user` - 用戶表
- `holders` - 持有人表
- `channels` - 渠道表

### 業務表
- `cash_accounts` - 現金帳戶表
- `customers` - 客戶表
- `purchase_records` - 買入記錄表
- `sales_records` - 銷售記錄表
- `ledger_entries` - 帳本記錄表
- `cash_logs` - 現金日誌表
- `transactions` - 交易記錄表
- `card_purchases` - 刷卡購買表

### FIFO 相關表
- `fifo_inventory` - FIFO 庫存表
- `fifo_sales_allocations` - FIFO 銷售分配表

### 可選表（如果存在）
- `profit_transactions` - 利潤交易表
- `pending_payments` - 待付款項表
- `delete_audit_logs` - 刪除審計日誌表

## 🔒 安全措施

1. **自動備份**：執行前會自動備份本地資料庫到 `instance/sales_system_v4_backup_YYYYMMDD_HHMMSS.db`
2. **確認提示**：執行前會要求確認，避免誤操作
3. **錯誤處理**：如果某個表讀取失敗，會跳過並繼續處理其他表

## 📍 本地資料庫位置

同步後的本地資料庫位於：
```
instance/sales_system_v4.db
```

## ⚠️ 注意事項

1. **資料替換**：此操作會完全替換本地資料庫的內容
2. **備份建議**：重要資料請先手動備份
3. **連線速度**：部署端資料庫位於美國，連線速度可能較慢
4. **資料完整性**：確保所有外鍵關係正確，資料會按正確順序插入

## 🔍 疑難排解

### 連線失敗
- 檢查網路連線
- 確認資料庫連接字串正確
- 檢查是否有防火牆阻擋
- 確認資料庫密碼是否正確

### 模組找不到
```bash
pip install -r requirements.txt
```

### 資料不一致
- 檢查錯誤訊息，確認哪些表同步失敗
- 查看備份檔案，必要時可以恢復

## 💡 使用建議

1. **測試前下拉**：在進行重要測試前，先下拉最新資料
2. **定期同步**：定期下拉資料以保持本地測試環境與部署端一致
3. **備份管理**：定期清理舊的備份檔案，節省空間

## 📝 範例輸出

```
================================================================================
📥 資料庫下拉工具
================================================================================

此工具會將部署端 PostgreSQL 的所有資料下拉到本地 SQLite

⚠️  警告：此操作會完全替換本地資料庫的內容！
   本地資料庫會自動備份到 instance/ 目錄

是否繼續？(yes/no): yes

================================================================================
📦 備份本地資料庫...
================================================================================
✅ 本地資料庫已備份: instance\sales_system_v4_backup_20241201_143022.db

================================================================================
[1/3] 從部署端資料庫讀取資料...
================================================================================
📖 正在讀取資料表...

✅ 讀取完成：
   Users: 2
   Holders: 3
   Channels: 5
   CashAccounts: 10
   Customers: 8
   PurchaseRecords: 150
   SalesRecords: 200
   ...

================================================================================
[2/3] 清空本地資料庫...
================================================================================
✅ 本地資料庫表已準備完成
🗑️  正在清空資料表...
   ✅ 已清空 profit_transactions
   ✅ 已清空 fifo_sales_allocations
   ...

================================================================================
[3/3] 寫入資料到本地資料庫...
================================================================================
📝 正在寫入資料...
   ✅ 2 筆 Users
   ✅ 3 筆 Holders
   ✅ 5 筆 Channels
   ...

✅ 資料下拉完成！
```

