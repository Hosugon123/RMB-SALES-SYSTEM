#!/usr/bin/env python3
"""
創建庫存日誌表的數據庫遷移腳本
"""

import sqlite3
import os
from datetime import datetime

def create_inventory_logs_table():
    """創建庫存日誌表"""
    
    # 檢查數據庫文件是否存在
    db_path = 'instance/rmb_sales.db'
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 開始創建庫存日誌表...")
        
        # 創建庫存日誌表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type VARCHAR(50) NOT NULL,
                batch_id INTEGER NOT NULL,
                change_amount DECIMAL(15,2) NOT NULL,
                balance_before DECIMAL(15,2) NOT NULL,
                balance_after DECIMAL(15,2) NOT NULL,
                note TEXT,
                operator_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES fifo_inventory (id),
                FOREIGN KEY (operator_id) REFERENCES users (id)
            )
        """)
        
        # 創建索引以提高查詢性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_logs_batch_id 
            ON inventory_logs (batch_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_logs_operation_type 
            ON inventory_logs (operation_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_logs_created_at 
            ON inventory_logs (created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_logs_operator_id 
            ON inventory_logs (operator_id)
        """)
        
        # 提交更改
        conn.commit()
        
        print("✅ 庫存日誌表創建成功！")
        
        # 檢查表是否創建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_logs'")
        if cursor.fetchone():
            print("✅ 表結構驗證成功")
            
            # 顯示表結構
            cursor.execute("PRAGMA table_info(inventory_logs)")
            columns = cursor.fetchall()
            
            print("\n📋 表結構:")
            print(f"{'欄位名':<15} {'類型':<15} {'可空':<8} {'主鍵':<8}")
            print("-" * 50)
            for col in columns:
                print(f"{col[1]:<15} {col[2]:<15} {'否' if col[3] else '是':<8} {'是' if col[5] else '否':<8}")
            
            # 檢查索引
            cursor.execute("PRAGMA index_list(inventory_logs)")
            indexes = cursor.fetchall()
            
            print(f"\n🔍 索引列表:")
            for idx in indexes:
                print(f"  - {idx[1]}")
            
        else:
            print("❌ 表創建失敗")
            return False
        
        # 插入一些示例數據（可選）
        insert_sample_data(cursor)
        
        conn.commit()
        conn.close()
        
        print("\n🎯 庫存日誌表創建完成！")
        return True
        
    except Exception as e:
        print(f"❌ 創建庫存日誌表時發生錯誤: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def insert_sample_data(cursor):
    """插入示例數據"""
    try:
        print("\n📝 插入示例數據...")
        
        # 檢查是否已有數據
        cursor.execute("SELECT COUNT(*) FROM inventory_logs")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("ℹ️ 表中已有數據，跳過示例數據插入")
            return
        
        # 插入示例數據
        sample_data = [
            ('add', 1, 1000.00, 0.00, 1000.00, '系統初始化示例數據', 1),
            ('add', 2, 500.00, 0.00, 500.00, '系統初始化示例數據', 1),
            ('withdraw', 1, -100.00, 1000.00, 900.00, '示例提款操作', 1),
            ('adjust', 2, 50.00, 500.00, 550.00, '示例庫存調整', 1),
            ('rate_change', 1, 0.00, 4.0000, 4.2000, '示例匯率變更', 1)
        ]
        
        cursor.executemany("""
            INSERT INTO inventory_logs 
            (operation_type, batch_id, change_amount, balance_before, balance_after, note, operator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_data)
        
        print(f"✅ 成功插入 {len(sample_data)} 條示例數據")
        
    except Exception as e:
        print(f"⚠️ 插入示例數據時發生錯誤: {str(e)}")

def verify_inventory_logs_table():
    """驗證庫存日誌表"""
    try:
        db_path = 'instance/rmb_sales.db'
        if not os.path.exists(db_path):
            print(f"❌ 數據庫文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 驗證庫存日誌表...")
        
        # 檢查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_logs'")
        if not cursor.fetchone():
            print("❌ 庫存日誌表不存在")
            return False
        
        # 檢查記錄數量
        cursor.execute("SELECT COUNT(*) FROM inventory_logs")
        count = cursor.fetchone()[0]
        print(f"✅ 表存在，共有 {count} 條記錄")
        
        # 檢查表結構
        cursor.execute("PRAGMA table_info(inventory_logs)")
        columns = cursor.fetchall()
        print(f"✅ 表有 {len(columns)} 個欄位")
        
        # 檢查索引
        cursor.execute("PRAGMA index_list(inventory_logs)")
        indexes = cursor.fetchall()
        print(f"✅ 表有 {len(indexes)} 個索引")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 驗證庫存日誌表時發生錯誤: {str(e)}")
        return False

def main():
    """主函數"""
    print("🚀 開始創建庫存日誌表...")
    print("=" * 60)
    
    # 創建表
    if create_inventory_logs_table():
        print("\n" + "=" * 60)
        
        # 驗證表
        if verify_inventory_logs_table():
            print("\n🎯 庫存日誌表創建和驗證完成！")
            print("\n📋 下一步:")
            print("1. 在 app.py 中導入並註冊 inventory_bp 藍圖")
            print("2. 在導航菜單中添加庫存管理頁面連結")
            print("3. 測試庫存管理功能")
        else:
            print("\n❌ 表驗證失敗")
    else:
        print("\n❌ 表創建失敗")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()



