# PowerShell 腳本：啟動應用並使用線上資料庫
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "啟動 RMB Sales System（使用線上資料庫）"
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host ""

# 設置環境變數
Write-Host "設置環境變數使用線上資料庫..." -ForegroundColor Green
$env:DATABASE_URL = "postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"

Write-Host "環境變數已設置" -ForegroundColor Yellow
Write-Host "啟動 Flask 應用..." -ForegroundColor Green
Write-Host ""

# 啟動應用
python app.py

