# 資料庫同步指南

## 問題說明

本地開發環境使用 SQLite，線上生產環境使用 PostgreSQL (Render)，兩者資料可能不同步。

## 解決方案

### 方案 1：使用改進版同步腳本（推薦）

#### 步驟 1：準備環境

1. **獲取 Render 資料庫連接字串**
   - 登入 [Render Dashboard](https://dashboard.render.com/)
   - 進入資料庫服務頁面
   - 複製 `Internal Database URL` 或 `External Database URL`

2. **設置環境變數（可選）**
   ```bash
   # Windows (PowerShell)
   $env:DATABASE_URL="postgresql+psycopg://user:password@host:port/database"
   
   # Windows (CMD)
   set DATABASE_URL=postgresql+psycopg://user:password@host:port/database
   
   # Linux/Mac
   export DATABASE_URL="postgresql+psycopg://user:password@host:port/database"
   ```

#### 步驟 2：執行同步腳本

```bash
python sync_data_improved.py
```

腳本會：
1. ✅ 自動備份本地資料庫
2. ✅ 從線上讀取所有資料
3. ✅ 清空本地資料庫
4. ✅ 寫入線上資料到本地
5. ✅ 顯示詳細進度和統計

### 方案 2：直接使用線上資料庫開發

如果需要立即使用線上最新資料，可以直接讓本地使用線上資料庫：

#### Windows (PowerShell)
```powershell
$env:DATABASE_URL="postgresql+psycopg://user:password@host:port/database"
python app.py
```

#### Windows (CMD)
```cmd
set DATABASE_URL=postgresql+psycopg://user:password@host:port/database
python app.py
```

#### Linux/Mac
```bash
export DATABASE_URL="postgresql+psycopg://user:password@host:port/database"
python app.py
```

**注意**：使用此方式時，本地修改會直接影響線上資料庫，請謹慎操作！

### 方案 3：使用其他現有腳本

如果改進版腳本有問題，可以嘗試：

1. **sync_online_to_local.py** - 從環境變數讀取 DATABASE_URL
   ```bash
   $env:DATABASE_URL="your_connection_string"
   python sync_online_to_local.py
   ```

2. **sync_render_to_local.py** - 已硬編碼連接字串（需要更新密碼）
   ```bash
   python sync_render_to_local.py
   ```

## 常見問題

### Q1: 同步失敗，顯示連接錯誤

**解決方案**：
1. 檢查 DATABASE_URL 格式是否正確
2. 確認連接字串包含 `+psycopg`（例如：`postgresql+psycopg://`）
3. 檢查網路連接和防火牆設置

### Q2: 同步後本地資料不完整

**解決方案**：
1. 檢查同步腳本的日誌輸出
2. 確認所有表都被讀取和寫入
3. 嘗試重新執行同步

### Q3: 同步後 ID 衝突

**解決方案**：
同步腳本會保留原始 ID，如果出現衝突：
1. 清空本地資料庫後重新同步
2. 或使用 SQLite 工具手動調整 ID

### Q4: 某些表同步失敗

**解決方案**：
1. 某些表可能不存在（如 ProfitTransaction, PendingPayment）
2. 腳本會自動跳過不存在的表
3. 這不會影響主要功能

## 同步前後檢查清單

### 同步前
- [ ] 確認本地沒有重要未保存的資料
- [ ] 確認已設置正確的 DATABASE_URL（如果使用環境變數）
- [ ] 確認網路連接正常

### 同步後
- [ ] 檢查同步統計是否正確
- [ ] 驗證本地應用程式可以正常啟動
- [ ] 檢查關鍵資料（帳戶餘額、客戶資訊等）是否正確
- [ ] 確認備份檔案已創建

## 推薦工作流程

### 日常開發
1. 使用本地 SQLite 進行開發
2. 定期（每天或每週）同步一次線上資料
3. 開發完成後推送到線上環境

### 緊急修復
1. 直接使用線上資料庫（設置 DATABASE_URL）
2. 修復問題
3. 推送到線上環境

### 資料恢復
1. 從備份檔案恢復（`instance/sales_system_v4_backup_*.db`）
2. 或從線上同步最新資料

## 自動化建議

可以創建批處理腳本自動執行同步：

### Windows (sync.bat)
```batch
@echo off
echo 開始同步資料庫...
set DATABASE_URL=your_connection_string
python sync_data_improved.py
pause
```

### Linux/Mac (sync.sh)
```bash
#!/bin/bash
echo "開始同步資料庫..."
export DATABASE_URL="your_connection_string"
python sync_data_improved.py
```

## 注意事項

⚠️ **重要警告**：
- 同步操作會**完全替換**本地資料庫內容
- 本地未保存的資料會**永久丟失**
- 同步前會自動備份，但仍建議手動備份重要資料
- 確保有正確的 DATABASE_URL 權限

✅ **最佳實踐**：
- 定期同步（建議每天一次）
- 同步前先測試應用程式
- 保留備份檔案至少一週
- 使用版本控制系統追蹤代碼變更

