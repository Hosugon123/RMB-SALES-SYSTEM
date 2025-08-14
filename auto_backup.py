#!/usr/bin/env python3
"""
自動備份腳本
設計用於在 Render 上定期執行
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backup_manager import BackupManager

def auto_backup():
    """自動備份主函數"""
    try:
        print(f"🚀 開始自動備份 - {datetime.now()}")
        
        # 初始化備份管理器
        manager = BackupManager()
        
        # 檢查是否需要備份
        status = manager.get_backup_status()
        latest_backup = status.get('latest_backup')
        
        if latest_backup:
            last_backup_time = latest_backup['modified']
            next_backup_time = last_backup_time + timedelta(hours=manager.config['backup_interval_hours'])
            
            if datetime.now() < next_backup_time:
                print(f"⏰ 距離下次備份還有: {next_backup_time - datetime.now()}")
                print("✅ 無需備份")
                return True
        
        # 創建備份
        print("📦 創建新備份...")
        success = manager.create_backup()
        
        if success:
            print("✅ 自動備份完成")
            
            # 顯示備份狀態
            new_status = manager.get_backup_status()
            print(f"📊 備份統計: 總共 {new_status['total_backups']} 個備份")
            
            return True
        else:
            print("❌ 自動備份失敗")
            return False
            
    except Exception as e:
        print(f"❌ 自動備份執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_disk_space():
    """檢查磁碟空間"""
    try:
        import shutil
        
        # 檢查當前目錄的磁碟空間
        total, used, free = shutil.disk_usage('.')
        
        print(f"💾 磁碟空間檢查:")
        print(f"  總空間: {total // (1024**3):.1f} GB")
        print(f"  已使用: {used // (1024**3):.1f} GB")
        print(f"  可用空間: {free // (1024**3):.1f} GB")
        
        # 如果可用空間少於 1GB，發出警告
        if free < 1024**3:
            print("⚠️  警告: 磁碟空間不足 1GB")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  無法檢查磁碟空間 (shutil 不可用)")
        return True

def cleanup_old_logs():
    """清理舊日誌檔案"""
    try:
        log_dir = Path('.')
        log_files = list(log_dir.glob('*.log'))
        
        # 刪除超過 30 天的日誌檔案
        cutoff_time = datetime.now() - timedelta(days=30)
        
        for log_file in log_files:
            if log_file.stat().st_mtime < cutoff_time.timestamp():
                log_file.unlink()
                print(f"🗑️  已刪除舊日誌: {log_file}")
                
    except Exception as e:
        print(f"⚠️  清理日誌失敗: {e}")

def main():
    """主函數"""
    print("=" * 50)
    print("🔄 自動備份系統啟動")
    print("=" * 50)
    
    # 檢查磁碟空間
    if not check_disk_space():
        print("❌ 磁碟空間不足，跳過備份")
        return 1
    
    # 清理舊日誌
    cleanup_old_logs()
    
    # 執行自動備份
    success = auto_backup()
    
    print("=" * 50)
    if success:
        print("✅ 自動備份系統執行完成")
        return 0
    else:
        print("❌ 自動備份系統執行失敗")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
