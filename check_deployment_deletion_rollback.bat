@echo off
REM 檢查部署環境的刪除記錄回滾情況
REM 需要設置 DATABASE_URL 環境變數

echo ========================================
echo 檢查部署環境刪除記錄回滾情況
echo ========================================
echo.

REM 檢查是否設置了 DATABASE_URL
if "%DATABASE_URL%"=="" (
    echo [ERROR] 未設置 DATABASE_URL 環境變數
    echo.
    echo 請先設置 DATABASE_URL 環境變數，例如：
    echo set DATABASE_URL=postgresql+psycopg://user:password@host:port/database
    echo.
    pause
    exit /b 1
)

echo [INFO] 使用部署環境資料庫
echo DATABASE_URL: %DATABASE_URL:~0,60%...
echo.

python check_deletion_rollback.py

pause

