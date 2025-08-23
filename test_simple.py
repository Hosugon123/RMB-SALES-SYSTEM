#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試腳本
"""

print("🚀 開始測試...")

try:
    import sqlite3
    print("✅ sqlite3 導入成功")
    
    # 檢查數據庫文件
    db_path = 'instance/sales_system_v4.db'
    if os.path.exists(db_path):
        print(f"✅ 數據庫文件存在: {db_path}")
        
        # 嘗試連接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ 找到 {len(tables)} 個表")
        
        conn.close()
    else:
        print(f"❌ 數據庫文件不存在: {db_path}")
        
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("🏁 測試完成")
