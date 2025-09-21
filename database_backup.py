#!/usr/bin/env python3
"""
PostgreSQL 資料庫備份腳本
從 Render PostgreSQL 資料庫備份資料到 Google Cloud Storage
"""

import os
import sys
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from google.cloud import storage
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 從環境變數獲取配置
        self.database_url = os.getenv('DATABASE_URL')
        self.gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        
        logger.info("=== 資料庫備份初始化 ===")
        logger.info(f"時間戳: {self.timestamp}")
        logger.info(f"GCS 儲存桶: {self.gcs_bucket_name}")
        
        # 驗證環境變數
        if not self.database_url:
            raise ValueError("DATABASE_URL 環境變數未設置")
        if not self.gcs_credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 環境變數未設置")
        if not self.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME 環境變數未設置")

    def connect_database(self):
        """連接到 PostgreSQL 資料庫"""
        try:
            logger.info("正在連接到 PostgreSQL 資料庫...")
            self.conn = psycopg2.connect(self.database_url)
            logger.info("✅ 資料庫連接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {str(e)}")
            return False

    def get_all_tables(self):
        """獲取所有資料表"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"找到 {len(tables)} 個資料表: {', '.join(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ 獲取資料表清單失敗: {str(e)}")
            return []

    def backup_table_to_excel(self, table_name):
        """備份單個資料表到 Excel"""
        try:
            logger.info(f"正在備份資料表: {table_name}")
            
            # 查詢資料表內容
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.conn)
            
            if df.empty:
                logger.info(f"⚠️ 資料表 {table_name} 為空，跳過備份")
                return None
            
            # 生成檔案名
            filename = f"{table_name}_backup_{self.timestamp}.xlsx"
            
            # 保存為 Excel
            df.to_excel(filename, index=False, engine='openpyxl')
            
            logger.info(f"✅ {table_name} 備份完成: {len(df)} 筆記錄 -> {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ 備份資料表 {table_name} 失敗: {str(e)}")
            return None

    def create_summary_report(self, backup_results):
        """創建備份摘要報告"""
        try:
            logger.info("正在創建備份摘要報告...")
            
            # 統計資訊
            summary_data = []
            total_records = 0
            
            for table_name, result in backup_results.items():
                if result['success']:
                    # 重新查詢統計資訊
                    cursor = self.conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    cursor.close()
                    
                    summary_data.append({
                        '資料表名稱': table_name,
                        '記錄數量': count,
                        '備份狀態': '成功',
                        '備份檔案': result['filename'],
                        '備份時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    total_records += count
                else:
                    summary_data.append({
                        '資料表名稱': table_name,
                        '記錄數量': 0,
                        '備份狀態': '失敗',
                        '備份檔案': '無',
                        '備份時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 添加總計行
            summary_data.append({
                '資料表名稱': '=== 總計 ===',
                '記錄數量': total_records,
                '備份狀態': f"{len([r for r in backup_results.values() if r['success']])}/{len(backup_results)} 成功",
                '備份檔案': f"共 {len([r for r in backup_results.values() if r['success']])} 個檔案",
                '備份時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 創建摘要 Excel
            df_summary = pd.DataFrame(summary_data)
            summary_filename = f"backup_summary_{self.timestamp}.xlsx"
            df_summary.to_excel(summary_filename, index=False, engine='openpyxl')
            
            logger.info(f"✅ 備份摘要報告創建完成: {summary_filename}")
            logger.info(f"📊 總共備份 {total_records} 筆記錄")
            
            return summary_filename
            
        except Exception as e:
            logger.error(f"❌ 創建摘要報告失敗: {str(e)}")
            return None

    def upload_to_gcs(self, local_file, gcs_path):
        """上傳檔案到 GCS"""
        try:
            client = storage.Client.from_service_account_json(self.gcs_credentials_path)
            bucket = client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(gcs_path)
            
            blob.upload_from_filename(local_file)
            
            # 設置元數據
            blob.metadata = {
                'source': 'database-backup',
                'timestamp': self.timestamp,
                'backup_type': 'postgresql'
            }
            blob.patch()
            
            logger.info(f"✅ 檔案上傳成功: gs://{self.gcs_bucket_name}/{gcs_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 檔案上傳失敗: {str(e)}")
            return False

    def cleanup_local_files(self, files):
        """清理本地檔案"""
        try:
            for file in files:
                if os.path.exists(file):
                    os.remove(file)
                    logger.info(f"🧹 已清理: {file}")
        except Exception as e:
            logger.error(f"❌ 清理檔案失敗: {str(e)}")

    def run_backup(self):
        """執行完整備份流程"""
        local_files = []
        
        try:
            logger.info("🚀 === 開始資料庫備份 ===")
            
            # 1. 連接資料庫
            if not self.connect_database():
                raise Exception("資料庫連接失敗")
            
            # 2. 獲取所有資料表
            tables = self.get_all_tables()
            if not tables:
                raise Exception("沒有找到資料表")
            
            # 3. 備份每個資料表
            backup_results = {}
            
            for table in tables:
                filename = self.backup_table_to_excel(table)
                if filename:
                    backup_results[table] = {
                        'success': True,
                        'filename': filename
                    }
                    local_files.append(filename)
                else:
                    backup_results[table] = {
                        'success': False,
                        'filename': None
                    }
            
            # 4. 創建摘要報告
            summary_file = self.create_summary_report(backup_results)
            if summary_file:
                local_files.append(summary_file)
            
            # 5. 上傳所有檔案到 GCS
            upload_success = 0
            for file in local_files:
                gcs_path = f"database_backups/{self.timestamp[:8]}/{file}"
                if self.upload_to_gcs(file, gcs_path):
                    upload_success += 1
            
            logger.info(f"📤 成功上傳 {upload_success}/{len(local_files)} 個檔案")
            
            # 關閉資料庫連接
            self.conn.close()
            logger.info("資料庫連接已關閉")
            
            logger.info("🎉 === 資料庫備份完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"❌ 資料庫備份失敗: {str(e)}")
            return False
            
        finally:
            # 清理本地檔案
            if local_files:
                self.cleanup_local_files(local_files)

def main():
    try:
        backup = DatabaseBackup()
        success = backup.run_backup()
        
        if success:
            logger.info("✅ 備份程式執行成功")
            sys.exit(0)
        else:
            logger.error("❌ 備份程式執行失敗")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 程式異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
