#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查備份中的銷售相關數據
"""

import sqlite3
import os

def check_backup_sales_data():
    """檢查備份中的銷售相關數據"""
    backup_path = 'recovery_backups/sales_system_v4_backup_20250823_001011.db'
    
    if not os.path.exists(backup_path):
        print(f"❌ 備份文件不存在: {backup_path}")
        return
    
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        print("🔍 檢查備份中的銷售相關數據...")
        
        # 檢查 sales_records 表
        print("\n📋 sales_records 表:")
        cursor.execute("SELECT COUNT(*) FROM sales_records;")
        sales_count = cursor.fetchone()[0]
        print(f"   記錄數: {sales_count}")
        
        if sales_count > 0:
            cursor.execute("SELECT * FROM sales_records LIMIT 5;")
            sales_records = cursor.fetchall()
            for i, record in enumerate(sales_records, 1):
                print(f"   記錄 {i}: {record}")
        
        # 檢查 fifo_sales_allocations 表
        print("\n📦 fifo_sales_allocations 表:")
        cursor.execute("SELECT COUNT(*) FROM fifo_sales_allocations;")
        allocations_count = cursor.fetchone()[0]
        print(f"   記錄數: {allocations_count}")
        
        if allocations_count > 0:
            cursor.execute("SELECT * FROM fifo_sales_allocations LIMIT 5;")
            allocations = cursor.fetchall()
            for i, record in enumerate(allocations, 1):
                print(f"   記錄 {i}: {record}")
        
        # 檢查 fifo_inventory 表
        print("\n🏪 fifo_inventory 表:")
        cursor.execute("SELECT COUNT(*) FROM fifo_inventory;")
        inventory_count = cursor.fetchone()[0]
        print(f"   記錄數: {inventory_count}")
        
        if inventory_count > 0:
            cursor.execute("SELECT * FROM fifo_inventory LIMIT 5;")
            inventories = cursor.fetchall()
            for i, record in enumerate(inventories, 1):
                print(f"   記錄 {i}: {record}")
        
        # 檢查 transactions 表
        print("\n💰 transactions 表:")
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        transactions_count = cursor.fetchone()[0]
        print(f"   記錄數: {transactions_count}")
        
        if transactions_count > 0:
            cursor.execute("SELECT * FROM transactions LIMIT 5;")
            transactions = cursor.fetchall()
            for i, record in enumerate(transactions, 1):
                print(f"   記錄 {i}: {record}")
        
        # 檢查是否有其他可能的銷售相關表
        print("\n🔍 檢查其他可能的銷售相關表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%sale%';")
        sale_tables = cursor.fetchall()
        if sale_tables:
            for table in sale_tables:
                print(f"   找到表: {table[0]}")
        else:
            print("   沒有找到名稱包含 'sale' 的表")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查備份銷售數據失敗: {e}")

if __name__ == "__main__":
    check_backup_sales_data()
