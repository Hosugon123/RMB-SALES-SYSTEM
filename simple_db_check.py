#!/usr/bin/env python3
"""
簡單的資料庫檢查腳本
"""

import os
import sqlite3
from datetime import datetime

def check_database():
    """檢查資料庫狀態"""
    db_path = "instance/sales_system_v4.db"
    
    print("🔍 檢查資料庫狀態...")
    print(f"時間: {datetime.now()}")
    print("=" * 40)
    
    # 檢查文件是否存在
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return
    
    # 檢查文件大小
    file_size = os.path.getsize(db_path)
    print(f"📁 文件路徑: {db_path}")
    print(f"📏 文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    # 檢查文件修改時間
    mtime = os.path.getmtime(db_path)
    mod_time = datetime.fromtimestamp(mtime)
    print(f"🕒 最後修改: {mod_time}")
    
    try:
        # 連接資料庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表格
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 表格數量: {len(tables)}")
        
        if tables:
            print("📋 表格列表:")
            total_records = 0
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    total_records += count
                    print(f"   {table_name}: {count} 條記錄")
                except Exception as e:
                    print(f"   {table_name}: 錯誤 - {e}")
            
            print(f"📈 總記錄數: {total_records}")
            
            if total_records == 0:
                print("⚠️  警告: 資料庫為空！可能被清空了")
            else:
                print("✅ 資料庫包含數據")
        else:
            print("⚠️  沒有找到任何表格")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")

def check_dangerous_files():
    """檢查危險文件"""
    print("\n🔍 檢查危險文件...")
    print("=" * 40)
    
    dangerous_patterns = [
        "init_database.py",
        "clear_all_data.py", 
        "clear_transactions.py",
        "quick_clear.py",
        "simple_clear.py"
    ]
    
    found_dangerous = []
    protected_dangerous = []
    
    for pattern in dangerous_patterns:
        if os.path.exists(pattern):
            found_dangerous.append(pattern)
        elif os.path.exists(pattern + ".DANGER"):
            protected_dangerous.append(pattern + ".DANGER")
    
    if found_dangerous:
        print("⚠️  發現未保護的危險文件:")
        for file in found_dangerous:
            print(f"   🔴 {file}")
    
    if protected_dangerous:
        print("✅ 已保護的危險文件:")
        for file in protected_dangerous:
            print(f"   🛡️  {file}")
    
    if not found_dangerous and not protected_dangerous:
        print("✅ 沒有發現危險文件")

if __name__ == "__main__":
    try:
        check_database()
        check_dangerous_files()
        print("\n" + "=" * 40)
        print("✅ 檢查完成")
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
