#!/usr/bin/env python3
"""
資料庫保護機制
防止危險的資料庫操作
"""

import os
import sys
from datetime import datetime

class DatabaseProtector:
    """資料庫保護器"""
    
    def __init__(self):
        self.dangerous_operations = [
            "DROP TABLE",
            "DELETE FROM",
            "TRUNCATE",
            "clear_all",
            "reset_database",
            "init_database"
        ]
    
    def check_operation_safety(self, operation):
        """檢查操作安全性"""
        operation_lower = operation.lower()
        
        for dangerous in self.dangerous_operations:
            if dangerous.lower() in operation_lower:
                print(f"🚨 檢測到危險操作: {dangerous}")
                print(f"   操作內容: {operation}")
                print(f"   時間: {datetime.now()}")
                return False
        
        return True
    
    def log_operation(self, operation, user=None):
        """記錄操作日誌"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] 操作: {operation}"
        if user:
            log_entry += f" | 用戶: {user}"
        
        with open('database_operations.log', 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        
        print(f"📝 操作已記錄: {operation}")

# 創建全局保護器實例
db_protector = DatabaseProtector()

def safe_database_operation(operation, user=None):
    """安全的資料庫操作包裝器"""
    if db_protector.check_operation_safety(operation):
        db_protector.log_operation(operation, user)
        return True
    else:
        print("❌ 危險操作已被阻止！")
        return False

def check_database_safety():
    """檢查資料庫安全性"""
    print("🛡️ 資料庫安全檢查...")
    
    # 檢查是否有危險腳本
    dangerous_files = [
        "clear_all_data.py",
        "reset_database.py",
        "init_database.py"
    ]
    
    found_dangerous = []
    for file in dangerous_files:
        if os.path.exists(file):
            found_dangerous.append(file)
            print(f"  ⚠️  發現危險文件: {file}")
    
    if found_dangerous:
        print(f"\n🚨 發現 {len(found_dangerous)} 個危險文件！")
        print("建議立即重命名或刪除這些文件")
    else:
        print("✅ 沒有發現危險文件")
    
    return found_dangerous

if __name__ == "__main__":
    print("🛡️ 資料庫保護機制已啟動")
    print("危險操作將被阻止並記錄")
    
    # 執行安全檢查
    check_database_safety()
