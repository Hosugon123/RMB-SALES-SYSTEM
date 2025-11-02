#!/bin/bash
# 使用線上資料庫運行本地應用

echo "設置環境變數使用線上資料庫..."
export DATABASE_URL="postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
echo "啟動應用..."
python app.py



