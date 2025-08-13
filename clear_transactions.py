#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理所有交易紀錄的腳本
清空銷售記錄、FIFO分配、現金日誌等，讓系統重新開始
"""

import sqlite3
import os

def clear_transactions():
    """清理所有交易紀錄"""
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 正在檢查數據庫中的交易紀錄...")
        
        # 檢查現有記錄數量
        tables_to_check = [
            ('sales_records', '銷售記錄'),
            ('fifo_sales_allocations', 'FIFO銷售分配'),
            ('cash_logs', '現金日誌'),
            ('ledger_entries', '記帳記錄'),
            ('fifo_inventory', 'FIFO庫存')
        ]
        
        for table_name, display_name in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 {display_name}: {count} 條")
        
        print("\n⚠️  警告：此操作將清空所有交易紀錄！")
        confirm = input("請輸入 'YES' 確認清空: ")
        
        if confirm != 'YES':
            print("❌ 操作已取消")
            return
        
        print("\n🧹 開始清理交易紀錄...")
        
        # 按順序清理相關表（注意外鍵約束）
        tables_to_clear = [
            'fifo_sales_allocations',  # 先清理FIFO分配
            'sales_records',           # 再清理銷售記錄
            'cash_logs',               # 清理現金日誌
            'ledger_entries',          # 清理記帳記錄
            'fifo_inventory'           # 最後清理FIFO庫存
        ]
        
        for table_name in tables_to_clear:
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = cursor.rowcount
            print(f"✅ 已清理 {table_name}: {deleted_count} 條記錄")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN (?, ?, ?, ?, ?)", 
                      tables_to_clear)
        
        # 提交更改
        conn.commit()
        
        print("\n🎉 交易紀錄清理完成！")
        print("📋 清理的內容包括：")
        print("   • 所有銷售記錄")
        print("   • FIFO庫存記錄")
        print("   • FIFO銷售分配")
        print("   • 現金日誌")
        print("   • 記帳記錄")
        print("\n💡 現在您可以重新開始記錄交易了！")
        
    except sqlite3.Error as e:
        print(f"❌ 數據庫操作失敗: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_transactions()
