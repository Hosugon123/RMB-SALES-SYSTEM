#!/usr/bin/env python3
"""
修復版 Render Cron Job - 移除 Selenium，只保留核心備份功能
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
    handlers=[
        logging.FileHandler('cron_job.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RenderCronJob:
    def __init__(self):
        """初始化 Cron Job"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 從環境變數獲取配置
        self.gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.target_url = os.getenv('TARGET_URL', 'https://www.google.com')
        
        # 驗證必要的環境變數
        if not self.gcs_credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 環境變數未設置")
        if not self.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME 環境變數未設置")
        
        logger.info(f"初始化完成 - 時間戳: {self.timestamp}")
        logger.info(f"目標網址: {self.target_url}")
        logger.info(f"GCS 儲存桶: {self.gcs_bucket_name}")

    def generate_excel_file(self):
        """生成範例 Excel 檔案"""
        try:
            logger.info("正在生成 Excel 檔案...")
            
            # 創建範例數據
            data = {
                '日期': [datetime.now().strftime('%Y-%m-%d')] * 10,
                '時間': [datetime.now().strftime('%H:%M:%S')] * 10,
                '備份類型': ['自動備份'] * 10,
                '狀態': ['成功'] * 10,
                '數量': [i+1 for i in range(10)],
                '大小(KB)': [100.50 + i*10 for i in range(10)],
                '備註': [f'備份項目_{i+1}' for i in range(10)]
            }
            
            # 創建 DataFrame
            df = pd.DataFrame(data)
            
            # 生成檔案名
            excel_filename = f"backup_data_{self.timestamp}.xlsx"
            
            # 保存為 Excel 檔案
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            
            logger.info(f"Excel 檔案生成成功: {excel_filename}")
            return excel_filename
            
        except Exception as e:
            logger.error(f"生成 Excel 檔案失敗: {str(e)}")
            return None

    def upload_to_gcs(self, local_file_path, gcs_file_name):
        """上傳檔案到 Google Cloud Storage"""
        try:
            logger.info(f"正在上傳檔案到 GCS: {local_file_path}")
            
            # 初始化 GCS 客戶端
            if self.gcs_credentials_path and os.path.exists(self.gcs_credentials_path):
                client = storage.Client.from_service_account_json(self.gcs_credentials_path)
            else:
                raise ValueError("無法找到有效的 GCS 認證資訊")
            
            bucket = client.bucket(self.gcs_bucket_name)
            
            # 創建 blob 對象
            blob = bucket.blob(gcs_file_name)
            
            # 上傳檔案
            blob.upload_from_filename(local_file_path)
            
            # 設置公開讀取權限（可選）
            blob.make_public()
            
            logger.info(f"檔案上傳成功: gs://{self.gcs_bucket_name}/{gcs_file_name}")
            return True
            
        except Exception as e:
            logger.error(f"上傳到 GCS 失敗: {str(e)}")
            return False

    def cleanup_local_files(self, file_paths):
        """清理本地臨時檔案"""
        try:
            logger.info("正在清理本地臨時檔案...")
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"已刪除本地檔案: {file_path}")
            
            logger.info("本地檔案清理完成")
            
        except Exception as e:
            logger.error(f"清理本地檔案失敗: {str(e)}")

    def run(self):
        """執行主要的 Cron Job 流程"""
        local_files = []
        
        try:
            logger.info("=== 開始執行 Render Cron Job ===")
            
            # 1. 生成 Excel 檔案
            excel_file = self.generate_excel_file()
            if excel_file:
                local_files.append(excel_file)
            else:
                raise Exception("Excel 檔案生成失敗")
            
            # 2. 上傳檔案到 GCS
            upload_success = True
            
            # 上傳 Excel 檔案
            excel_gcs_name = f"excel/{excel_file}"
            if not self.upload_to_gcs(excel_file, excel_gcs_name):
                upload_success = False
            
            if not upload_success:
                raise Exception("檔案上傳失敗")
            
            logger.info("=== Cron Job 執行完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"Cron Job 執行失敗: {str(e)}")
            return False
            
        finally:
            # 清理本地檔案
            if local_files:
                self.cleanup_local_files(local_files)

def main():
    """主函數"""
    try:
        # 創建並執行 Cron Job
        cron_job = RenderCronJob()
        success = cron_job.run()
        
        if success:
            logger.info("Cron Job 執行成功")
            sys.exit(0)
        else:
            logger.error("Cron Job 執行失敗")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程式執行失敗: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
