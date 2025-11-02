# 資料庫同步指南

## 從 Render PostgreSQL 同步到本地 SQLite

### 方法 1：使用專業工具（推薦）

#### 方案 A：使用 pgAdmin
1. 下載並安裝 [pgAdmin](https://www.pgadmin.org/)
2. 添加 Render 資料庫連接：
   - Host: `dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com`
   - Port: `5432`
   - Database: `rmb_database_v4`
   - Username: `rmb_user`
   - Password: `BGvPp5PwQ3WRnoLCTzW2`
3. 使用 pgAdmin 的「備份/還原」功能匯出所有資料
4. 將匯出的資料轉換為 SQLite 格式

#### 方案 B：使用 psycopg2 + sqlite3
如果您的電腦已安裝 PostgreSQL 客戶端工具，可以使用 `pg_dump` 匯出資料。

### 方法 2：使用 Python 腳本（需要完整配置）

由於 Flask-SQLAlchemy 的模型在單一資料庫連接時初始化，同步兩個不同類型的資料庫需要特殊的處理。

**注意**：所有自動同步腳本都需要：
1. 正確配置線上資料庫連接
2. 正確配置本地資料庫
3. 處理所有模型的外鍵關係
4. 確保資料一致性

### 方法 3：手動同步關鍵資料（快速方案）

如果只需要快速測試，可以：

1. **直接使用線上資料庫進行本地開發**
   - 在本地環境設置 `DATABASE_URL` 環境變數
   - 指向 Render PostgreSQL
   - 這樣本地就會使用線上資料庫

2. **導出關鍵表格進行測試**
   - 使用 Render Dashboard 的資料庫瀏覽器
   - 匯出 CSV 檔案
   - 手動導入到本地 SQLite

### 目前可用的腳本

1. `sync_online_to_local.py` - 完整同步腳本（複雜）
2. `simple_sync_online.py` - 簡化版（測試用）
3. `sync_render_to_local.py` - 改進版（推薦嘗試）

### 使用 Render Dashboard 的資料庫工具

最簡單的方式是：

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 選擇您的資料庫服務
3. 使用「Data」標籤或「Database Browser」
4. 手動匯出需要的資料表格
5. 使用 CSV 或 Excel 格式匯入到本地 SQLite

### 警告

⚠️ **重要**：
- 同步操作會完全替換本地資料庫
- 建議先備份本地資料庫
- PostgreSQL 和 SQLite 的資料類型可能不完全相容
- 某些功能（如自動遞增 ID）可能需要特殊處理

### 建議

對於日常開發，建議：
1. **開發環境**：使用本地 SQLite
2. **測試環境**：使用線上 PostgreSQL（設置 DATABASE_URL）
3. **資料同步**：僅在需要時手動操作

### 緊急情況

如果需要立即使用線上資料，最簡單的方式是：

```bash
# 設置環境變數使用線上資料庫
export DATABASE_URL="postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"

# 運行本地應用
python app.py
```

這樣本地就會直接使用線上資料庫，無需同步。


