#!/usr/bin/env python3
"""
Render Cron Job Script
生成 Excel 檔案、網頁截圖並上傳到 Google Cloud Storage
"""

import os
import sys
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
        self.driver = None
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

    def setup_chrome_driver(self):
        """設置 Headless Chrome 驅動程式"""
        try:
            logger.info("正在設置 Chrome 驅動程式...")
            
            chrome_options = Options()
            
            # Render 容器環境所需的 Chrome 選項
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # 自動安裝 ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # 創建 WebDriver 實例
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("Chrome 驅動程式設置成功")
            return True
            
        except Exception as e:
            logger.error(f"設置 Chrome 驅動程式失敗: {str(e)}")
            return False

    def generate_excel_file(self):
        """生成範例 Excel 檔案"""
        try:
            logger.info("正在生成 Excel 檔案...")
            
            # 創建範例數據
            data = {
                '日期': [datetime.now().strftime('%Y-%m-%d')] * 10,
                '時間': [datetime.now().strftime('%H:%M:%S')] * 10,
                '產品名稱': [f'產品_{i+1}' for i in range(10)],
                '數量': [i+1 for i in range(10)],
                '單價': [100.50 + i*10 for i in range(10)],
                '總價': [(100.50 + i*10) * (i+1) for i in range(10)],
                '備註': [f'備註_{i+1}' for i in range(10)]
            }
            
            # 創建 DataFrame
            df = pd.DataFrame(data)
            
            # 生成檔案名
            excel_filename = f"sample_data_{self.timestamp}.xlsx"
            
            # 保存為 Excel 檔案
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            
            logger.info(f"Excel 檔案生成成功: {excel_filename}")
            return excel_filename
            
        except Exception as e:
            logger.error(f"生成 Excel 檔案失敗: {str(e)}")
            return None

    def take_screenshot(self):
        """截取網頁截圖"""
        try:
            logger.info(f"正在截取網頁截圖: {self.target_url}")
            
            # 導航到目標網址
            self.driver.get(self.target_url)
            
            # 等待頁面載入
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待額外時間確保頁面完全載入
            time.sleep(3)
            
            # 生成截圖檔案名
            screenshot_filename = f"screenshot_{self.timestamp}.png"
            
            # 截取全頁面截圖
            self.driver.save_screenshot(screenshot_filename)
            
            logger.info(f"截圖成功: {screenshot_filename}")
            return screenshot_filename
            
        except Exception as e:
            logger.error(f"截圖失敗: {str(e)}")
            return None

    def upload_to_gcs(self, local_file_path, gcs_file_name):
        """上傳檔案到 Google Cloud Storage"""
        try:
            logger.info(f"正在上傳檔案到 GCS: {local_file_path}")
            
            # 初始化 GCS 客戶端
            client = storage.Client.from_service_account_json(self.gcs_credentials_path)
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
            
            # 1. 設置 Chrome 驅動程式
            if not self.setup_chrome_driver():
                raise Exception("無法設置 Chrome 驅動程式")
            
            # 2. 生成 Excel 檔案
            excel_file = self.generate_excel_file()
            if excel_file:
                local_files.append(excel_file)
            else:
                raise Exception("Excel 檔案生成失敗")
            
            # 3. 截取網頁截圖
            screenshot_file = self.take_screenshot()
            if screenshot_file:
                local_files.append(screenshot_file)
            else:
                raise Exception("截圖失敗")
            
            # 4. 上傳檔案到 GCS
            upload_success = True
            
            # 上傳 Excel 檔案
            excel_gcs_name = f"excel/{excel_file}"
            if not self.upload_to_gcs(excel_file, excel_gcs_name):
                upload_success = False
            
            # 上傳截圖檔案
            screenshot_gcs_name = f"screenshots/{screenshot_file}"
            if not self.upload_to_gcs(screenshot_file, screenshot_gcs_name):
                upload_success = False
            
            if not upload_success:
                raise Exception("部分檔案上傳失敗")
            
            logger.info("=== Cron Job 執行完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"Cron Job 執行失敗: {str(e)}")
            return False
            
        finally:
            # 5. 清理資源
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Chrome 驅動程式已關閉")
                except Exception as e:
                    logger.error(f"關閉 Chrome 驅動程式失敗: {str(e)}")
            
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
