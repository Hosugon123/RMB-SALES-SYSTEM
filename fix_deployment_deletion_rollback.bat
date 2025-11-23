@echo off
REM 修復部署環境的刪除記錄回滾問題
REM 需要設置 DATABASE_URL 環境變數

echo ========================================
echo 修復部署環境刪除記錄回滾問題
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
echo [WARNING] 這將直接修改部署環境的資料庫！
echo.

set /p confirm="確認執行修復？(yes/no): "
if /i not "%confirm%"=="yes" (
    echo 取消修復
    pause
    exit /b 0
)

python fix_deletion_rollback.py --auto-fix

pause

