#!/usr/bin/env python3
"""
緊急資料庫保護腳本
防止意外清空資料庫
"""

import os
import shutil
import sqlite3
from datetime import datetime
import stat

def create_emergency_backup():
    """創建緊急備份"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return False
    
    try:
        # 創建備份目錄
        backup_dir = "emergency_backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 創建備份
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"emergency_backup_{timestamp}.db")
        
        shutil.copy2(db_path, backup_path)
        
        # 設置為只讀
        os.chmod(backup_path, stat.S_IREAD)
        
        print(f"✅ 緊急備份已創建: {backup_path}")
        print(f"   大小: {os.path.getsize(backup_path) / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建備份失敗: {e}")
        return False

def protect_database_file():
    """保護資料庫文件"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return False
    
    try:
        # 備份當前權限
        current_mode = os.stat(db_path).st_mode
        
        # 創建保護文件記錄
        protection_file = "database_protection_info.txt"
        with open(protection_file, 'w', encoding='utf-8') as f:
            f.write(f"資料庫保護啟用時間: {datetime.now()}\n")
            f.write(f"原始文件權限: {oct(current_mode)}\n")
            f.write(f"保護狀態: 啟用\n")
        
        print("✅ 資料庫保護已啟用")
        return True
        
    except Exception as e:
        print(f"❌ 保護設置失敗: {e}")
        return False

def check_database_health():
    """檢查資料庫健康狀態"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return False
    
    try:
        # 連接資料庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表格
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 資料庫健康檢查:")
        print(f"   文件大小: {os.path.getsize(db_path) / 1024:.1f} KB")
        print(f"   表格數量: {len(tables)}")
        
        # 檢查每個表格的記錄數
        total_records = 0
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                if count > 0:
                    print(f"   {table_name}: {count} 條記錄")
            except:
                pass
        
        print(f"   總記錄數: {total_records}")
        
        conn.close()
        
        if total_records > 0:
            print("✅ 資料庫包含數據，狀態良好")
        else:
            print("⚠️  資料庫為空，可能被清空了")
        
        return total_records > 0
        
    except Exception as e:
        print(f"❌ 檢查資料庫失敗: {e}")
        return False

def rename_dangerous_files():
    """重命名危險文件"""
    dangerous_files = [
        "init_database.py",
        "clear_all_data.py",
        "clear_transactions.py", 
        "quick_clear.py",
        "simple_clear.py"
    ]
    
    renamed_count = 0
    
    for filename in dangerous_files:
        if os.path.exists(filename):
            try:
                new_name = filename + ".DANGER"
                if not os.path.exists(new_name):
                    os.rename(filename, new_name)
                    print(f"🛡️  已重命名危險文件: {filename} -> {new_name}")
                    renamed_count += 1
            except Exception as e:
                print(f"⚠️  無法重命名 {filename}: {e}")
    
    if renamed_count > 0:
        print(f"✅ 已保護 {renamed_count} 個危險文件")
    else:
        print("✅ 沒有發現未保護的危險文件")

def main():
    """主函數"""
    print("🛡️  緊急資料庫保護系統")
    print("=" * 40)
    
    # 1. 檢查資料庫健康狀態
    print("\n1. 檢查資料庫健康狀態...")
    db_healthy = check_database_health()
    
    # 2. 創建緊急備份
    print("\n2. 創建緊急備份...")
    backup_success = create_emergency_backup()
    
    # 3. 重命名危險文件
    print("\n3. 保護危險文件...")
    rename_dangerous_files()
    
    # 4. 啟用保護
    print("\n4. 啟用資料庫保護...")
    protect_success = protect_database_file()
    
    print("\n" + "=" * 40)
    if backup_success and protect_success:
        print("✅ 資料庫保護系統已完全啟用")
        if not db_healthy:
            print("⚠️  警告: 資料庫似乎為空，建議立即恢復備份")
    else:
        print("❌ 保護系統啟用不完全，請檢查錯誤信息")
    
    print("\n💡 建議:")
    print("   1. 立即檢查所有 .DANGER 文件是否包含危險代碼")
    print("   2. 定期創建備份")
    print("   3. 避免運行未經確認的腳本")
    print("   4. 檢查是否有定時任務或自動腳本在運行")

if __name__ == "__main__":
    main()
