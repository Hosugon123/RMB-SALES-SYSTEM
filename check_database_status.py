#!/usr/bin/env python3
"""
資料庫狀態檢查腳本
用於診斷數據丟失問題
"""

import os
import sys
from datetime import datetime

def check_database_status():
    """檢查資料庫狀態"""
    try:
        print("🔍 開始檢查資料庫狀態...")
        print(f"⏰ 檢查時間: {datetime.now()}")
        
        # 檢查資料庫檔案
        db_path = os.path.join('instance', 'sales_system_v4.db')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
            print(f"✅ 資料庫檔案存在: {db_path}")
            print(f"📊 檔案大小: {db_size} bytes")
            print(f"🕒 最後修改: {db_mtime}")
        else:
            print(f"❌ 資料庫檔案不存在: {db_path}")
            return
        
        # 檢查實例目錄
        instance_dir = 'instance'
        if os.path.exists(instance_dir):
            files = os.listdir(instance_dir)
            print(f"📁 實例目錄內容: {files}")
        else:
            print(f"❌ 實例目錄不存在: {instance_dir}")
        
        # 檢查環境變數
        print("\n🔧 環境變數檢查:")
        env_vars = [
            'FLASK_ENV', 'FLASK_DEBUG', 'DATABASE_URL', 
            'SQLALCHEMY_DATABASE_URI', 'SECRET_KEY'
        ]
        for var in env_vars:
            value = os.environ.get(var, '未設定')
            print(f"  {var}: {value}")
        
        # 檢查 Python 進程
        print("\n🐍 Python 進程檢查:")
        try:
            import psutil
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            print(f"  當前進程 ID: {current_pid}")
            print(f"  進程名稱: {current_process.name()}")
            print(f"  進程命令: {' '.join(current_process.cmdline())}")
            
            # 檢查是否有其他 Python 進程
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            print(f"  Python 進程數量: {len(python_processes)}")
            for proc in python_processes:
                print(f"    PID {proc['pid']}: {' '.join(proc['cmdline'])}")
                
        except ImportError:
            print("  psutil 未安裝，無法檢查進程")
        
        # 檢查檔案鎖定
        print("\n🔒 檔案鎖定檢查:")
        try:
            import fcntl
            with open(db_path, 'rb') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    print("✅ 資料庫檔案未被鎖定")
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except IOError:
                    print("❌ 資料庫檔案被鎖定")
        except ImportError:
            print("  fcntl 未安裝，無法檢查檔案鎖定")
        
        print("\n✅ 資料庫狀態檢查完成")
        
    except Exception as e:
        print(f"❌ 檢查資料庫狀態時出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_status()
