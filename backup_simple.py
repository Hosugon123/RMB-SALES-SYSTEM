#!/usr/bin/env python3
"""
簡化版備份腳本 - 無 Selenium 依賴
"""

import os
import sys
import pandas as pd
from datetime import datetime
from google.cloud import storage
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 獲取環境變數
        gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        
        logger.info("=== 簡化版備份開始 ===")
        logger.info(f"時間戳: {timestamp}")
        logger.info(f"認證檔案: {gcs_credentials_path}")
        logger.info(f"儲存桶: {gcs_bucket_name}")
        
        # 檢查環境變數
        if not gcs_credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 未設置")
        if not gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME 未設置")
        
        # 檢查認證檔案
        if not os.path.exists(gcs_credentials_path):
            raise FileNotFoundError(f"認證檔案不存在: {gcs_credentials_path}")
        
        logger.info("✅ 環境檢查通過")
        
        # 創建測試數據
        data = {
            '備份時間': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 5,
            '狀態': ['成功'] * 5,
            '項目': [f'項目_{i+1}' for i in range(5)],
            '大小': [100 + i*50 for i in range(5)]
        }
        
        df = pd.DataFrame(data)
        filename = f"backup_{timestamp}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        
        logger.info(f"✅ Excel 檔案創建成功: {filename}")
        
        # 上傳到 GCS
        client = storage.Client.from_service_account_json(gcs_credentials_path)
        bucket = client.bucket(gcs_bucket_name)
        
        # 測試儲存桶連線
        if not bucket.exists():
            raise ValueError(f"儲存桶 '{gcs_bucket_name}' 不存在")
        
        logger.info("✅ GCS 連線成功")
        
        # 上傳檔案
        blob = bucket.blob(f"backups/{filename}")
        blob.upload_from_filename(filename)
        
        logger.info(f"✅ 檔案上傳成功: gs://{gcs_bucket_name}/backups/{filename}")
        
        # 清理本地檔案
        os.remove(filename)
        logger.info("✅ 本地檔案已清理")
        
        logger.info("🎉 === 備份完成 ===")
        
    except Exception as e:
        logger.error(f"❌ 備份失敗: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
