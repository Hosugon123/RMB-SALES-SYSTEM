# 快速使用線上資料庫指南

## ✅ 已完成的工作

1. ✅ 修正了 SalesRecord 創建時 LedgerEntry 記錄的問題
2. ✅ 修正了 Cash Management 流水餘額的正向累積計算
3. ✅ 建立了資料庫同步工具

## 🚀 如何讓本地使用線上資料庫

### 方法 1：使用批次檔（最簡單）

**Windows PowerShell 或 CMD**：
```bash
.\run_with_online_db.bat
```

### 方法 2：手動設置環境變數

**PowerShell**：
```powershell
$env:DATABASE_URL="postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
python app.py
```

**CMD**：
```cmd
set DATABASE_URL=postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4
python app.py
```

**Linux/Mac**：
```bash
export DATABASE_URL="postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
python app.py
```

### 方法 3：使用 .env 檔案（推薦長期使用）

建立 `.env` 檔案：
```
DATABASE_URL=postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4
```

然後運行：
```bash
python app.py
```

## 📋 驗證連線成功

啟動成功後，您應該會看到：
```
使用資料庫連接字串: postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs...
```

這表示已經連接到線上資料庫了！

## ⚠️ 注意事項

1. **資料安全**：使用線上資料庫時，所有操作都會直接影響線上資料
2. **備份建議**：重要操作前建議先備份
3. **連線速度**：線上資料庫位於美國，連線速度可能較慢
4. **依賴套件**：確保已安裝所有依賴：`pip install -r requirements.txt`

## 🔍 疑難排解

### 連線失敗
- 檢查網路連線
- 確認資料庫連接字串正確
- 檢查是否有防火牆阻擋

### 模組找不到
```bash
pip install -r requirements.txt
```

### 資料庫表格不存在
應用會在首次啟動時自動建立表格

## 📞 需要幫助？

如果遇到問題，請提供錯誤訊息。


