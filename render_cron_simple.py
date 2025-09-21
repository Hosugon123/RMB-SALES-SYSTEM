#!/usr/bin/env python3
"""
簡化版 Render Cron Job - 用於測試基本功能
只測試 GCS 連線和檔案上傳，不使用 Selenium
"""

import os
import sys
import pandas as pd
import json
import tempfile
from datetime import datetime
from google.cloud import storage
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleCronJob:
    def __init__(self):
        """初始化簡化版 Cron Job"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 從環境變數獲取配置
        self.gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.gcs_credentials_json = os.getenv('GCS_CREDENTIALS_JSON')
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.target_url = os.getenv('TARGET_URL', 'https://www.google.com')
        
        logger.info(f"初始化完成 - 時間戳: {self.timestamp}")
        logger.info(f"GCS 儲存桶: {self.gcs_bucket_name}")
        logger.info(f"認證檔案路徑: {self.gcs_credentials_path}")
        
        # 檢查環境變數
        self.check_environment()

    def check_environment(self):
        """檢查環境變數和檔案"""
        logger.info("=== 環境檢查 ===")
        
        # 檢查 GCS 儲存桶名稱
        if not self.gcs_bucket_name:
            raise ValueError("❌ GCS_BUCKET_NAME 環境變數未設置")
        logger.info(f"✅ GCS_BUCKET_NAME: {self.gcs_bucket_name}")
        
        # 檢查認證檔案
        if self.gcs_credentials_path:
            if os.path.exists(self.gcs_credentials_path):
                logger.info(f"✅ 認證檔案存在: {self.gcs_credentials_path}")
            else:
                logger.error(f"❌ 認證檔案不存在: {self.gcs_credentials_path}")
                raise FileNotFoundError(f"認證檔案不存在: {self.gcs_credentials_path}")
        elif self.gcs_credentials_json:
            logger.info("✅ 使用 JSON 格式認證")
        else:
            raise ValueError("❌ 需要設置 GOOGLE_APPLICATION_CREDENTIALS 或 GCS_CREDENTIALS_JSON")

    def create_gcs_client(self):
        """創建 GCS 客戶端"""
        try:
            if self.gcs_credentials_path and os.path.exists(self.gcs_credentials_path):
                logger.info("使用檔案路徑認證")
                client = storage.Client.from_service_account_json(self.gcs_credentials_path)
            elif self.gcs_credentials_json:
                logger.info("使用 JSON 內容認證")
                # 創建臨時檔案
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    json.dump(json.loads(self.gcs_credentials_json), temp_file)
                    temp_path = temp_file.name
                
                client = storage.Client.from_service_account_json(temp_path)
                os.unlink(temp_path)  # 清理臨時檔案
            else:
                raise ValueError("無法創建 GCS 客戶端")
            
            logger.info("✅ GCS 客戶端創建成功")
            return client
            
        except Exception as e:
            logger.error(f"❌ 創建 GCS 客戶端失敗: {str(e)}")
            raise

    def test_gcs_connection(self):
        """測試 GCS 連線"""
        try:
            logger.info("=== 測試 GCS 連線 ===")
            
            client = self.create_gcs_client()
            bucket = client.bucket(self.gcs_bucket_name)
            
            # 測試儲存桶是否存在
            if bucket.exists():
                logger.info(f"✅ 儲存桶 '{self.gcs_bucket_name}' 存在")
                
                # 列出現有檔案
                blobs = list(bucket.list_blobs(max_results=5))
                logger.info(f"✅ 儲存桶中有 {len(blobs)} 個檔案")
                
                return True
            else:
                logger.error(f"❌ 儲存桶 '{self.gcs_bucket_name}' 不存在")
                return False
                
        except Exception as e:
            logger.error(f"❌ GCS 連線測試失敗: {str(e)}")
            return False

    def generate_test_excel(self):
        """生成測試用 Excel 檔案"""
        try:
            logger.info("=== 生成測試 Excel 檔案 ===")
            
            # 創建測試數據
            data = {
                '測試時間': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 5,
                '狀態': ['測試成功'] * 5,
                '數值': [i * 10 for i in range(1, 6)],
                '備註': [f'測試項目 {i}' for i in range(1, 6)]
            }
            
            df = pd.DataFrame(data)
            filename = f"test_backup_{self.timestamp}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            
            logger.info(f"✅ Excel 檔案生成成功: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Excel 檔案生成失敗: {str(e)}")
            return None

    def upload_to_gcs(self, local_file, gcs_path):
        """上傳檔案到 GCS"""
        try:
            logger.info(f"=== 上傳檔案到 GCS ===")
            logger.info(f"本地檔案: {local_file}")
            logger.info(f"GCS 路徑: {gcs_path}")
            
            client = self.create_gcs_client()
            bucket = client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(gcs_path)
            
            # 上傳檔案
            blob.upload_from_filename(local_file)
            
            logger.info(f"✅ 檔案上傳成功: gs://{self.gcs_bucket_name}/{gcs_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 檔案上傳失敗: {str(e)}")
            return False

    def run(self):
        """執行簡化版 Cron Job"""
        try:
            logger.info("🚀 === 開始執行簡化版 Cron Job ===")
            
            # 1. 測試 GCS 連線
            if not self.test_gcs_connection():
                raise Exception("GCS 連線測試失敗")
            
            # 2. 生成測試檔案
            excel_file = self.generate_test_excel()
            if not excel_file:
                raise Exception("測試檔案生成失敗")
            
            # 3. 上傳到 GCS
            gcs_path = f"test_backups/{excel_file}"
            if not self.upload_to_gcs(excel_file, gcs_path):
                raise Exception("檔案上傳失敗")
            
            # 4. 清理本地檔案
            if os.path.exists(excel_file):
                os.remove(excel_file)
                logger.info(f"✅ 已清理本地檔案: {excel_file}")
            
            logger.info("🎉 === 簡化版 Cron Job 執行成功 ===")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cron Job 執行失敗: {str(e)}")
            return False

def main():
    """主函數"""
    try:
        cron_job = SimpleCronJob()
        success = cron_job.run()
        
        if success:
            logger.info("✅ 程式執行成功")
            sys.exit(0)
        else:
            logger.error("❌ 程式執行失敗")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 程式異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
