#!/usr/bin/env python3
"""
三合一資料管理系統
1. 備份保護 - 完整資料備份到 GCS
2. 減少資料庫大小 - 歷史資料歸檔
3. 歷史資料查詢 - 保持查詢能力
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

class ArchiveBackupSystem:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 配置參數
        self.KEEP_MONTHS = 6  # 資料庫保留最近6個月
        self.archive_date = datetime.now() - timedelta(days=30 * self.KEEP_MONTHS)
        
        # 環境變數
        self.database_url = os.getenv('DATABASE_URL')
        self.gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        
        logger.info("=== 三合一資料管理系統初始化 ===")
        logger.info(f"保留資料: 最近 {self.KEEP_MONTHS} 個月")
        logger.info(f"歸檔界線: {self.archive_date.strftime('%Y-%m-%d')}")
        
        # 需要歷史歸檔的資料表（可配置）
        self.archivable_tables = {
            'sales_records': 'created_at',      # 銷售記錄
            'purchase_records': 'created_at',   # 採購記錄
            'cash_logs': 'created_at',          # 現金記錄
            'ledger_entries': 'created_at',     # 分類帳條目
            # 'users': None,                    # 用戶表不歸檔
            # 'customers': None,                # 客戶表不歸檔
        }

    def connect_database(self):
        """連接資料庫"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("✅ 資料庫連接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {str(e)}")
            return False

    def step1_full_backup(self):
        """步驟1: 完整備份保護"""
        logger.info("🔒 === 步驟1: 完整備份保護 ===")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            backup_files = []
            
            for table in tables:
                logger.info(f"備份資料表: {table}")
                df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
                
                if not df.empty:
                    filename = f"full_backup_{table}_{self.timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                    backup_files.append(filename)
                    
                    # 上傳到 GCS
                    gcs_path = f"full_backups/{self.timestamp[:8]}/{filename}"
                    self.upload_to_gcs(filename, gcs_path)
            
            logger.info(f"✅ 完整備份完成: {len(backup_files)} 個檔案")
            return backup_files
            
        except Exception as e:
            logger.error(f"❌ 完整備份失敗: {str(e)}")
            return []

    def step2_archive_old_data(self):
        """步驟2: 歷史資料歸檔"""
        logger.info("📦 === 步驟2: 歷史資料歸檔 ===")
        
        archived_files = []
        space_saved = 0
        
        for table, date_column in self.archivable_tables.items():
            if not date_column:
                continue
                
            try:
                logger.info(f"處理資料表: {table}")
                
                # 查詢舊資料
                archive_query = f"""
                    SELECT * FROM {table} 
                    WHERE {date_column} < %s
                    ORDER BY {date_column}
                """
                
                df_archive = pd.read_sql_query(
                    archive_query, 
                    self.conn, 
                    params=[self.archive_date]
                )
                
                if df_archive.empty:
                    logger.info(f"⚪ {table}: 沒有需要歸檔的資料")
                    continue
                
                # 保存歷史資料到 Excel
                archive_filename = f"archive_{table}_{self.timestamp}.xlsx"
                df_archive.to_excel(archive_filename, index=False, engine='openpyxl')
                archived_files.append(archive_filename)
                
                # 上傳歷史資料到 GCS
                gcs_path = f"archives/{self.timestamp[:6]}/{archive_filename}"
                self.upload_to_gcs(archive_filename, gcs_path)
                
                # 計算要刪除的記錄數
                record_count = len(df_archive)
                
                # 刪除資料庫中的舊資料
                cursor = self.conn.cursor()
                delete_query = f"DELETE FROM {table} WHERE {date_column} < %s"
                cursor.execute(delete_query, [self.archive_date])
                deleted_count = cursor.rowcount
                self.conn.commit()
                cursor.close()
                
                space_saved += deleted_count
                
                logger.info(f"✅ {table}: 歸檔 {record_count} 筆，刪除 {deleted_count} 筆")
                
            except Exception as e:
                logger.error(f"❌ 歸檔 {table} 失敗: {str(e)}")
                self.conn.rollback()
        
        logger.info(f"📉 總計節省資料庫空間: 約 {space_saved} 筆記錄")
        return archived_files

    def step3_create_query_index(self):
        """步驟3: 創建歷史資料查詢索引"""
        logger.info("🔍 === 步驟3: 歷史資料查詢索引 ===")
        
        try:
            # 創建查詢索引
            query_index = {
                '備份日期': self.timestamp[:8],
                '歸檔界線': self.archive_date.strftime('%Y-%m-%d'),
                '保留政策': f'最近 {self.KEEP_MONTHS} 個月',
                '歸檔位置': f'gs://{self.gcs_bucket_name}/archives/{self.timestamp[:6]}/',
                '完整備份位置': f'gs://{self.gcs_bucket_name}/full_backups/{self.timestamp[:8]}/',
                '查詢說明': '歷史資料可從 GCS archives 資料夾下載查詢'
            }
            
            # 統計當前資料庫狀態
            cursor = self.conn.cursor()
            db_stats = []
            
            for table in self.archivable_tables.keys():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                current_count = cursor.fetchone()[0]
                
                db_stats.append({
                    '資料表': table,
                    '當前記錄數': current_count,
                    '狀態': '已歸檔' if current_count > 0 else '空'
                })
            
            cursor.close()
            
            # 創建查詢指南 Excel
            with pd.ExcelWriter(f"query_index_{self.timestamp}.xlsx", engine='openpyxl') as writer:
                # 基本資訊
                pd.DataFrame([query_index]).to_excel(writer, sheet_name='基本資訊', index=False)
                
                # 資料庫狀態
                pd.DataFrame(db_stats).to_excel(writer, sheet_name='資料庫狀態', index=False)
                
                # 查詢說明
                query_guide = pd.DataFrame([
                    {'步驟': 1, '說明': '查詢最近6個月資料：直接使用主資料庫'},
                    {'步驟': 2, '說明': '查詢歷史資料：從 GCS archives 下載對應檔案'},
                    {'步驟': 3, '說明': '完整資料查詢：結合資料庫 + GCS 歷史檔案'},
                    {'步驟': 4, '說明': '緊急恢復：使用 full_backups 完整備份'}
                ])
                query_guide.to_excel(writer, sheet_name='查詢指南', index=False)
            
            # 上傳查詢索引
            index_filename = f"query_index_{self.timestamp}.xlsx"
            gcs_path = f"query_indexes/{index_filename}"
            self.upload_to_gcs(index_filename, gcs_path)
            
            logger.info("✅ 歷史資料查詢索引創建完成")
            return index_filename
            
        except Exception as e:
            logger.error(f"❌ 創建查詢索引失敗: {str(e)}")
            return None

    def upload_to_gcs(self, local_file, gcs_path):
        """上傳到 GCS"""
        try:
            client = storage.Client.from_service_account_json(self.gcs_credentials_path)
            bucket = client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(gcs_path)
            
            blob.upload_from_filename(local_file)
            blob.metadata = {
                'source': 'archive-backup-system',
                'timestamp': self.timestamp,
                'type': gcs_path.split('/')[0]
            }
            blob.patch()
            
            return True
        except Exception as e:
            logger.error(f"❌ 上傳失敗 {local_file}: {str(e)}")
            return False

    def cleanup_local_files(self, files):
        """清理本地檔案"""
        total_size = 0
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                total_size += size
                os.remove(file)
                logger.info(f"🧹 已清理: {file} ({size/1024:.1f} KB)")
        
        logger.info(f"💾 總共節省本地空間: {total_size/1024:.1f} KB")

    def run_complete_system(self):
        """執行完整的三合一系統"""
        all_files = []
        
        try:
            logger.info("🚀 === 三合一資料管理系統開始 ===")
            
            # 連接資料庫
            if not self.connect_database():
                raise Exception("資料庫連接失敗")
            
            # 步驟1: 完整備份保護
            backup_files = self.step1_full_backup()
            all_files.extend(backup_files)
            
            # 步驟2: 歷史資料歸檔（減少資料庫大小）
            archive_files = self.step2_archive_old_data()
            all_files.extend(archive_files)
            
            # 步驟3: 創建查詢索引
            index_file = self.step3_create_query_index()
            if index_file:
                all_files.append(index_file)
            
            self.conn.close()
            
            logger.info("🎉 === 三合一系統執行完成 ===")
            logger.info("✅ 備份保護: 完整資料已備份")
            logger.info("📉 資料庫大小: 歷史資料已歸檔")
            logger.info("🔍 歷史查詢: 查詢索引已建立")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 系統執行失敗: {str(e)}")
            return False
            
        finally:
            # 清理本地檔案
            if all_files:
                self.cleanup_local_files(all_files)

def main():
    try:
        system = ArchiveBackupSystem()
        success = system.run_complete_system()
        
        if success:
            logger.info("✅ 三合一系統執行成功")
            sys.exit(0)
        else:
            logger.error("❌ 三合一系統執行失敗")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 程式異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
