@echo off
chcp 65001 >nul
echo ================================================================================
echo 資料庫下拉工具
echo ================================================================================
echo.
echo 請選擇版本：
echo 1. 標準版（詳細錯誤處理）
echo 2. 簡化版（使用 bulk_insert_mappings，更穩定）
echo.
set /p choice="請選擇 (1/2，預設 2): "

if "%choice%"=="1" (
    python pull_deployment_db.py
) else (
    python pull_deployment_db_simple.py
)
pause

