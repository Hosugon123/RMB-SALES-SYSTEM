@echo off
chcp 65001 >nul
echo ================================================================================
echo 啟動 RMB Sales System（使用線上資料庫）
echo ================================================================================
echo.
echo 設置環境變數使用線上資料庫...
set DATABASE_URL=postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4
echo 環境變數已設置
echo.
echo 啟動 Flask 應用...
echo.
py app.py
pause

