#!/bin/bash

# Render 服務設定腳本
# 用於在 Render 上部署 Cron Job

echo "🚀 開始設定 Render Cron Job..."

# 檢查必要的環境變數
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ 錯誤: GOOGLE_APPLICATION_CREDENTIALS 環境變數未設定"
    echo "請在 Render Dashboard 中設定此環境變數"
    exit 1
fi

if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "❌ 錯誤: GCS_BUCKET_NAME 環境變數未設定"
    echo "請在 Render Dashboard 中設定此環境變數"
    exit 1
fi

echo "✅ 環境變數檢查通過"

# 安裝依賴套件
echo "📦 安裝 Python 依賴套件..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依賴套件安裝成功"
else
    echo "❌ 依賴套件安裝失敗"
    exit 1
fi

# 檢查 Google Cloud Storage 認證
echo "🔐 檢查 GCS 認證..."
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ GCS 認證檔案存在"
else
    echo "❌ GCS 認證檔案不存在: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "請確保已正確上傳服務帳戶密鑰檔案"
    exit 1
fi

# 測試腳本執行
echo "🧪 測試腳本執行..."
python -c "
import sys
sys.path.append('.')
from render_cron_job import RenderCronJob
print('✅ 腳本導入成功')
"

if [ $? -eq 0 ]; then
    echo "✅ 腳本測試通過"
else
    echo "❌ 腳本測試失敗"
    exit 1
fi

echo "🎉 Render Cron Job 設定完成！"
echo ""
echo "📋 下一步："
echo "1. 在 Render Dashboard 中設定環境變數"
echo "2. 上傳服務帳戶密鑰 JSON 檔案"
echo "3. 設定 Cron Job 執行時間"
echo "4. 部署並測試"
