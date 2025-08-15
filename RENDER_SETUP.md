# Render 部署設置指南

## 📋 在 Render 上設置持久化 PostgreSQL 資料庫

### 1. 創建 PostgreSQL 資料庫

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 點擊 "New +" → "PostgreSQL"
3. 設置：
   - **Name**: `rmb-sales-system-db`
   - **Database**: `rmb_sales_system`
   - **User**: `rmb_user`
   - **Region**: 選擇距離最近的區域
   - **Plan**: Free（免費方案）

### 2. 獲取資料庫連接資訊

創建完成後，在資料庫的 "Info" 頁面找到：
- **Internal Database URL**: 以 `postgres://` 開頭的連接字串

### 3. 設置 Web Service 環境變數

在您的 Web Service 設置中：

1. 進入 "Environment" 頁面
2. 添加環境變數：
   ```
   DATABASE_URL = [您的 Internal Database URL]
   SECRET_KEY = your_secret_key_here
   ```

### 4. 第一次部署後的數據導入

1. 部署完成後，訪問：
   ```
   https://您的網站域名.onrender.com/import_data.html
   ```

2. 點擊 "🚀 開始導入數據" 來導入您的本地數據

### 5. 資料庫遷移（如需要）

如果需要手動執行資料庫遷移：

1. 在 Render Web Service 的 Shell 中執行：
   ```bash
   flask db upgrade
   ```

## 🔧 本地開發

本地開發仍使用 SQLite，不需要額外配置。

## ✅ 驗證設置

部署完成後：
1. 檢查網站是否正常訪問
2. 登入系統
3. 檢查資料是否持久化（重新部署後資料不會消失）

## 📞 故障排除

如果遇到問題：
1. 檢查 Render 的 Logs 頁面
2. 確認 DATABASE_URL 環境變數設置正確
3. 確認 PostgreSQL 資料庫狀態為 "Available"
