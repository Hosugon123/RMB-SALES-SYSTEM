#!/bin/bash
# 檢查部署環境的刪除記錄回滾情況
# 在 Render 部署環境中，DATABASE_URL 會自動設置

echo "========================================"
echo "檢查部署環境刪除記錄回滾情況"
echo "========================================"
echo ""

# 檢查是否設置了 DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] 未設置 DATABASE_URL 環境變數"
    echo ""
    echo "在 Render 部署環境中，DATABASE_URL 通常會自動設置。"
    echo "如果未設置，請檢查 Render Dashboard 的環境變數設置。"
    echo ""
    exit 1
fi

echo "[INFO] 使用部署環境資料庫"
echo "DATABASE_URL: ${DATABASE_URL:0:60}..."
echo ""

python3 check_deletion_rollback.py

