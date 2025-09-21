#!/usr/bin/env python3
"""
Render Cron Job - 使用環境變數 JSON 認證
避免 Secret Files 路徑問題
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

class RenderCronJob:
    def __init__(self):
        """初始化 Cron Job - 使用環境變數 JSON"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 從環境變數獲取配置
        self.gcs_credentials_json = os.getenv('GCS_CREDENTIALS_JSON')
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.target_url = os.getenv('TARGET_URL', 'https://www.google.com')
        
        logger.info(f"初始化完成 - 時間戳: {self.timestamp}")
        logger.info(f"GCS 儲存桶: {self.gcs_bucket_name}")
        
        # 檢查必要的環境變數
        if not self.gcs_credentials_json:
            raise ValueError("GCS_CREDENTIALS_JSON 環境變數未設置")
        if not self.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME 環境變數未設置")

    def create_gcs_client(self):
        """創建 GCS 客戶端 - 使用環境變數 JSON"""
        try:
            logger.info("創建 GCS 客戶端...")
            
            # 解析 JSON 認證
            creds_data = json.loads(self.gcs_credentials_json)
            
            # 創建臨時檔案
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(creds_data, temp_file)
                temp_path = temp_file.name
            
            # 創建客戶端
            client = storage.Client.from_service_account_json(temp_path)
            
            # 清理臨時檔案
            os.unlink(temp_path)
            
            logger.info("✅ GCS 客戶端創建成功")
            return client
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 格式錯誤: {str(e)}")
            raise
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
                logger.info(f"✅ 儲存桶 '{self.gcs_bucket_name}' 連線成功")
                
                # 列出現有檔案
                blobs = list(bucket.list_blobs(max_results=5))
                logger.info(f"📊 儲存桶中有 {len(blobs)} 個檔案")
                
                if blobs:
                    logger.info("最近的檔案:")
                    for blob in blobs[:3]:
                        logger.info(f"  - {blob.name} ({blob.time_created})")
                
                return True
            else:
                logger.error(f"❌ 儲存桶 '{self.gcs_bucket_name}' 不存在")
                return False
                
        except Exception as e:
            logger.error(f"❌ GCS 連線測試失敗: {str(e)}")
            return False

    def generate_backup_excel(self):
        """生成備份 Excel 檔案"""
        try:
            logger.info("=== 生成備份 Excel 檔案 ===")
            
            # 創建備份數據
            data = {
                '備份時間': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 5,
                '備份類型': ['自動備份'] * 5,
                '狀態': ['成功'] * 5,
                '檔案大小(KB)': [100 + i*50 for i in range(5)],
                '備註': [f'備份項目 {i+1}' for i in range(5)]
            }
            
            df = pd.DataFrame(data)
            filename = f"backup_report_{self.timestamp}.xlsx"
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
            
            # 設置檔案元數據
            blob.metadata = {
                'source': 'render-cron-job',
                'timestamp': self.timestamp,
                'backup_type': 'automated'
            }
            blob.patch()
            
            logger.info(f"✅ 檔案上傳成功: gs://{self.gcs_bucket_name}/{gcs_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 檔案上傳失敗: {str(e)}")
            return False

    def cleanup_local_files(self, file_paths):
        """清理本地檔案"""
        try:
            logger.info("=== 清理本地檔案 ===")
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"✅ 已刪除: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ 清理檔案失敗: {str(e)}")

    def run(self):
        """執行主要的 Cron Job 流程"""
        local_files = []
        
        try:
            logger.info("🚀 === 開始執行 Render Cron Job ===")
            
            # 1. 測試 GCS 連線
            if not self.test_gcs_connection():
                raise Exception("GCS 連線測試失敗")
            
            # 2. 生成備份檔案
            excel_file = self.generate_backup_excel()
            if not excel_file:
                raise Exception("備份檔案生成失敗")
            
            local_files.append(excel_file)
            
            # 3. 上傳到 GCS
            gcs_path = f"backups/{excel_file}"
            if not self.upload_to_gcs(excel_file, gcs_path):
                raise Exception("檔案上傳失敗")
            
            logger.info("🎉 === Cron Job 執行成功 ===")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cron Job 執行失敗: {str(e)}")
            return False
            
        finally:
            # 清理本地檔案
            if local_files:
                self.cleanup_local_files(local_files)

def main():
    """主函數"""
    try:
        cron_job = RenderCronJob()
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
