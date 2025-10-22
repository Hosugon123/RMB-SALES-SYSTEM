#!/bin/bash
# Render 部署啟動腳本

echo "🚀 開始 PostgreSQL 欄位修復..."
python fix_postgresql_columns.py

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL 欄位修復完成"
    echo "🚀 啟動 Flask 應用程式..."
    gunicorn app:app
else
    echo "❌ PostgreSQL 欄位修復失敗"
    exit 1
fi
