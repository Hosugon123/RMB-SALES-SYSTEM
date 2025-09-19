#!/usr/bin/env python3
"""
GCS 備份系統檢查腳本
用於驗證 Render Cron Job 是否正常備份到 Google Cloud Storage
"""

import os
import sys
from datetime import datetime
from google.cloud import storage
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """檢查必要的環境變數"""
    logger.info("🔍 檢查環境變數...")
    
    required_vars = {
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        'GCS_BUCKET_NAME': os.getenv('GCS_BUCKET_NAME'),
        'TARGET_URL': os.getenv('TARGET_URL', 'https://www.google.com')
    }
    
    all_good = True
    for var_name, var_value in required_vars.items():
        if var_value:
            logger.info(f"✅ {var_name}: {var_value}")
        else:
            logger.error(f"❌ {var_name}: 未設定")
            all_good = False
    
    return all_good

def check_gcs_credentials():
    """檢查 GCS 認證檔案"""
    logger.info("🔐 檢查 GCS 認證...")
    
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS 未設定")
        return False
    
    if not os.path.exists(creds_path):
        logger.error(f"❌ 認證檔案不存在: {creds_path}")
        return False
    
    logger.info(f"✅ 認證檔案存在: {creds_path}")
    return True

def check_gcs_connection():
    """檢查 GCS 連線"""
    logger.info("🌐 檢查 GCS 連線...")
    
    try:
        client = storage.Client.from_service_account_json(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        bucket = client.bucket(bucket_name)
        
        # 測試連線
        if bucket.exists():
            logger.info(f"✅ GCS 連線成功，儲存桶 '{bucket_name}' 存在")
            return True
        else:
            logger.error(f"❌ 儲存桶 '{bucket_name}' 不存在")
            return False
            
    except Exception as e:
        logger.error(f"❌ GCS 連線失敗: {str(e)}")
        return False

def check_recent_backups():
    """檢查最近的備份檔案"""
    logger.info("📁 檢查最近的備份檔案...")
    
    try:
        client = storage.Client.from_service_account_json(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        bucket = client.bucket(bucket_name)
        
        # 檢查 Excel 檔案
        excel_blobs = list(bucket.list_blobs(prefix='excel/'))
        if excel_blobs:
            latest_excel = max(excel_blobs, key=lambda x: x.time_created)
            logger.info(f"✅ 最新 Excel 檔案: {latest_excel.name} (創建時間: {latest_excel.time_created})")
        else:
            logger.warning("⚠️ 沒有找到 Excel 檔案")
        
        # 檢查截圖檔案
        screenshot_blobs = list(bucket.list_blobs(prefix='screenshots/'))
        if screenshot_blobs:
            latest_screenshot = max(screenshot_blobs, key=lambda x: x.time_created)
            logger.info(f"✅ 最新截圖檔案: {latest_screenshot.name} (創建時間: {latest_screenshot.time_created})")
        else:
            logger.warning("⚠️ 沒有找到截圖檔案")
        
        return len(excel_blobs) > 0 and len(screenshot_blobs) > 0
        
    except Exception as e:
        logger.error(f"❌ 檢查備份檔案失敗: {str(e)}")
        return False

def check_render_logs():
    """檢查 Render 日誌（需要手動提供）"""
    logger.info("📋 Render 日誌檢查...")
    logger.info("請在 Render Dashboard 中檢查以下項目：")
    logger.info("1. Cron Job 是否成功創建")
    logger.info("2. 最後執行時間")
    logger.info("3. 執行狀態（成功/失敗）")
    logger.info("4. 錯誤日誌內容")
    logger.info("5. 資源使用情況")

def main():
    """主檢查函數"""
    logger.info("🚀 開始 GCS 備份系統檢查...")
    logger.info("=" * 50)
    
    checks = [
        ("環境變數", check_environment_variables),
        ("GCS 認證", check_gcs_credentials),
        ("GCS 連線", check_gcs_connection),
        ("備份檔案", check_recent_backups),
    ]
    
    results = []
    for check_name, check_func in checks:
        logger.info(f"\n--- 檢查 {check_name} ---")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ 檢查 {check_name} 時發生錯誤: {str(e)}")
            results.append((check_name, False))
    
    # 檢查 Render 日誌
    check_render_logs()
    
    # 總結報告
    logger.info("\n" + "=" * 50)
    logger.info("📊 檢查結果總結:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 所有檢查都通過！您的 GCS 備份系統運行正常。")
    else:
        logger.info("\n⚠️ 部分檢查失敗，請根據上述錯誤訊息進行修復。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
