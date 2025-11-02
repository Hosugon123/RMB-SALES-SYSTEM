# 從備份檔案恢復資料庫

## 🎯 您目前的備份檔案

您有一個 PostgreSQL 自訂格式的備份檔案：`2025-11-01T16_53Z.dir.tar.gz`

這是一個 PostgreSQL pg_dump 的壓縮備份，已經解壓到 `backup_temp` 目錄。

## ⚠️ 問題

要恢復這種格式的備份，需要：
1. **本地安裝 PostgreSQL** 或
2. **能夠連接到線上資料庫** 且
3. **使用 `pg_restore` 命令**

但是目前我們無法從本機連接到 Render PostgreSQL（SSL 連接問題）。

## ✅ 建議方案

### 方案 1：使用 Render Shell 進行恢復（最簡單）

在 Render Dashboard 上直接恢復：

1. 登入 [Render Dashboard](https://dashboard.render.com)
2. 選擇您的資料庫服務
3. 點擊「Shell」標籤
4. 上傳備份檔案到 Render
5. 使用 `pg_restore` 命令恢復

### 方案 2：使用 Excel 備份（如果有的話）

如果您之前有使用 `database_backup.py` 產生 Excel 備份：

1. 檢查 GCS 儲存桶
2. 下載 Excel 備份檔案
3. 使用 `import_database_api` 導入

### 方案 3：使用現有本地資料庫

**最簡單的方案**：繼續使用本地 SQLite 資料庫進行開發。

所有代碼修正已經完成，可以正常使用本地資料庫測試所有功能。

## 🚀 現在可以做的事情

1. **直接啟動本地應用**：不使用 DATABASE_URL，自動使用本地 SQLite
2. **測試所有功能**：確保修正的程式碼正常工作
3. **部署到 Render**：代碼正確後，直接部署到 Render

## 💡 建議

**不要花時間解決 Render 外部連接問題**，因為：
- 免費版 Render PostgreSQL 通常不支援外部連接
- 本地開發使用 SQLite 足夠
- 線上測試可以在 Render 環境進行

請直接使用本地 SQLite 資料庫繼續開發！


