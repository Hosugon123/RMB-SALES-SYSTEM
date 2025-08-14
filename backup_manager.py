#!/usr/bin/env python3
"""
資料庫備份管理系統
支援本地備份、雲端同步和自動清理
"""

import os
import sys
import shutil
import sqlite3
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class BackupManager:
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # 備份配置
        self.config = {
            'max_backups': 10,  # 保留的最大備份數量
            'backup_interval_hours': 24,  # 備份間隔（小時）
            'compress_backups': True,  # 是否壓縮備份
            'cloud_sync': False,  # 是否啟用雲端同步
            'cloud_drive_path': None,  # 雲端硬碟路徑
        }
        
        # 載入配置
        self.load_config()
    
    def load_config(self):
        """載入備份配置"""
        config_file = Path('backup_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                logging.info("✅ 備份配置已載入")
            except Exception as e:
                logging.error(f"❌ 載入配置失敗: {e}")
    
    def save_config(self):
        """保存備份配置"""
        try:
            with open('backup_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info("✅ 備份配置已保存")
        except Exception as e:
            logging.error(f"❌ 保存配置失敗: {e}")
    
    def create_backup(self, backup_name=None):
        """創建資料庫備份"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}"
            
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # 備份資料庫
            db_source = Path('instance/sales_system_v4.db')
            if not db_source.exists():
                logging.error("❌ 資料庫檔案不存在")
                return False
            
            db_backup = backup_path / 'sales_system_v4.db'
            shutil.copy2(db_source, db_backup)
            
            # 備份配置檔案
            config_files = [
                'backup_config.json',
                'requirements.txt',
                '.flaskenv'
            ]
            
            for config_file in config_files:
                if Path(config_file).exists():
                    shutil.copy2(config_file, backup_path)
            
            # 創建備份資訊檔案
            backup_info = {
                'backup_time': datetime.now().isoformat(),
                'backup_name': backup_name,
                'database_size': db_source.stat().st_size,
                'files_backed_up': [f.name for f in backup_path.iterdir()],
                'version': '1.0.0'
            }
            
            with open(backup_path / 'backup_info.json', 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # 壓縮備份（如果啟用）
            if self.config['compress_backups']:
                self.compress_backup(backup_path)
                # 刪除未壓縮的目錄
                shutil.rmtree(backup_path)
                backup_path = Path(f"{backup_path}.zip")
            
            logging.info(f"✅ 備份創建成功: {backup_path}")
            
            # 清理舊備份
            self.cleanup_old_backups()
            
            # 雲端同步（如果啟用）
            if self.config['cloud_sync']:
                self.sync_to_cloud(backup_path)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ 創建備份失敗: {e}")
            return False
    
    def compress_backup(self, backup_path):
        """壓縮備份目錄"""
        try:
            zip_path = f"{backup_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            logging.info(f"✅ 備份已壓縮: {zip_path}")
            
        except Exception as e:
            logging.error(f"❌ 壓縮備份失敗: {e}")
    
    def cleanup_old_backups(self):
        """清理舊備份"""
        try:
            # 獲取所有備份檔案
            backup_files = []
            for file_path in self.backup_dir.iterdir():
                if file_path.is_file() and (file_path.suffix == '.zip' or file_path.is_dir()):
                    backup_files.append(file_path)
            
            # 按修改時間排序
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 刪除超出數量限制的備份
            if len(backup_files) > self.config['max_backups']:
                for old_backup in backup_files[self.config['max_backups']:]:
                    if old_backup.is_dir():
                        shutil.rmtree(old_backup)
                    else:
                        old_backup.unlink()
                    logging.info(f"🗑️  已刪除舊備份: {old_backup}")
            
        except Exception as e:
            logging.error(f"❌ 清理舊備份失敗: {e}")
    
    def sync_to_cloud(self, backup_path):
        """同步到雲端硬碟"""
        if not self.config['cloud_drive_path']:
            logging.warning("⚠️  雲端硬碟路徑未設定")
            return
        
        try:
            cloud_path = Path(self.config['cloud_drive_path'])
            if not cloud_path.exists():
                logging.error(f"❌ 雲端硬碟路徑不存在: {cloud_path}")
                return
            
            # 複製備份到雲端
            cloud_backup = cloud_path / backup_path.name
            if backup_path.is_dir():
                shutil.copytree(backup_path, cloud_backup, dirs_exist_ok=True)
            else:
                shutil.copy2(backup_path, cloud_backup)
            
            logging.info(f"☁️  備份已同步到雲端: {cloud_backup}")
            
        except Exception as e:
            logging.error(f"❌ 雲端同步失敗: {e}")
    
    def restore_backup(self, backup_name):
        """從備份恢復資料庫"""
        try:
            backup_path = self.backup_dir / backup_name
            
            # 檢查備份是否存在
            if not backup_path.exists():
                if Path(f"{backup_path}.zip").exists():
                    backup_path = Path(f"{backup_path}.zip")
                else:
                    logging.error(f"❌ 備份不存在: {backup_name}")
                    return False
            
            # 如果是壓縮檔案，先解壓
            if backup_path.suffix == '.zip':
                extract_path = backup_path.with_suffix('')
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                backup_path = extract_path
            
            # 恢復資料庫
            db_backup = backup_path / 'sales_system_v4.db'
            if not db_backup.exists():
                logging.error("❌ 備份中找不到資料庫檔案")
                return False
            
            # 備份當前資料庫
            current_db = Path('instance/sales_system_v4.db')
            if current_db.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safety_backup = Path(f"instance/sales_system_v4_safety_{timestamp}.db")
                shutil.copy2(current_db, safety_backup)
                logging.info(f"✅ 當前資料庫已備份: {safety_backup}")
            
            # 恢復備份
            shutil.copy2(db_backup, current_db)
            logging.info(f"✅ 資料庫已從備份恢復: {backup_name}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ 恢復備份失敗: {e}")
            return False
    
    def list_backups(self):
        """列出所有備份"""
        try:
            backups = []
            for file_path in self.backup_dir.iterdir():
                if file_path.is_file() and (file_path.suffix == '.zip' or file_path.is_dir()):
                    stat = file_path.stat()
                    backup_info = {
                        'name': file_path.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'type': 'zip' if file_path.suffix == '.zip' else 'folder'
                    }
                    backups.append(backup_info)
            
            # 按修改時間排序
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
            return backups
            
        except Exception as e:
            logging.error(f"❌ 列出備份失敗: {e}")
            return []
    
    def get_backup_status(self):
        """獲取備份狀態"""
        try:
            backups = self.list_backups()
            latest_backup = backups[0] if backups else None
            
            status = {
                'total_backups': len(backups),
                'latest_backup': latest_backup,
                'backup_dir': str(self.backup_dir.absolute()),
                'config': self.config,
                'next_backup_time': None
            }
            
            if latest_backup:
                next_backup = latest_backup['modified'] + timedelta(hours=self.config['backup_interval_hours'])
                status['next_backup_time'] = next_backup
            
            return status
            
        except Exception as e:
            logging.error(f"❌ 獲取備份狀態失敗: {e}")
            return {}

def create_backup_command():
    """創建備份的命令行介面"""
    import argparse
    
    parser = argparse.ArgumentParser(description='資料庫備份管理工具')
    parser.add_argument('action', choices=['create', 'restore', 'list', 'status', 'config'],
                       help='執行的操作')
    parser.add_argument('--name', help='備份名稱')
    parser.add_argument('--max-backups', type=int, help='最大備份數量')
    parser.add_argument('--interval', type=int, help='備份間隔（小時）')
    parser.add_argument('--cloud-sync', action='store_true', help='啟用雲端同步')
    parser.add_argument('--cloud-path', help='雲端硬碟路徑')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == 'create':
        success = manager.create_backup(args.name)
        if success:
            print("✅ 備份創建成功")
        else:
            print("❌ 備份創建失敗")
    
    elif args.action == 'restore':
        if not args.name:
            print("❌ 請指定要恢復的備份名稱")
            return
        
        success = manager.restore_backup(args.name)
        if success:
            print("✅ 備份恢復成功")
        else:
            print("❌ 備份恢復失敗")
    
    elif args.action == 'list':
        backups = manager.list_backups()
        if backups:
            print(f"📋 找到 {len(backups)} 個備份:")
            for backup in backups:
                print(f"  {backup['name']} - {backup['modified']} ({backup['size']} bytes)")
        else:
            print("📋 沒有找到備份")
    
    elif args.action == 'status':
        status = manager.get_backup_status()
        print("📊 備份狀態:")
        print(f"  總備份數量: {status['total_backups']}")
        print(f"  備份目錄: {status['backup_dir']}")
        if status['latest_backup']:
            print(f"  最新備份: {status['latest_backup']['name']}")
            print(f"  備份時間: {status['latest_backup']['modified']}")
        if status['next_backup_time']:
            print(f"  下次備份: {status['next_backup_time']}")
    
    elif args.action == 'config':
        if args.max_backups:
            manager.config['max_backups'] = args.max_backups
        if args.interval:
            manager.config['backup_interval_hours'] = args.interval
        if args.cloud_sync is not None:
            manager.config['cloud_sync'] = args.cloud_sync
        if args.cloud_path:
            manager.config['cloud_drive_path'] = args.cloud_path
        
        manager.save_config()
        print("✅ 配置已更新")

if __name__ == "__main__":
    create_backup_command()
