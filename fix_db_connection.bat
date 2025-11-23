@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo 修復資料庫連接 - 切換到本地資料庫
echo ================================================================================
echo.
echo 此腳本將：
echo 1. 移除 DATABASE_URL 環境變數（使用本地 SQLite）
echo 2. 驗證本地資料庫內容
echo.
pause

echo.
echo 正在移除 DATABASE_URL 環境變數...
set DATABASE_URL=
echo DATABASE_URL 已清除（僅在當前會話中有效）
echo.

echo 正在驗證本地資料庫...
python verify_db_sync.py

echo.
echo ================================================================================
echo 重要提示：
echo ================================================================================
echo 1. 環境變數的清除只在當前 PowerShell/CMD 會話中有效
echo 2. 如果要在新的終端中使用本地資料庫，請：
echo    - 不要設置 DATABASE_URL 環境變數
echo    - 或者使用以下命令清除： set DATABASE_URL=
echo 3. 重啟應用程式以使用本地資料庫
echo.
pause

