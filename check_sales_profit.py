#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_sales_profit():
    db_path = 'instance/sales_system.db'
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 檢查最近的銷售記錄
        cursor.execute('''
            SELECT id, customer_name, rmb_amount, twd_amount, created_at 
            FROM sales_record 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        sales = cursor.fetchall()
        
        print('=== 最近5筆銷售記錄 ===')
        if not sales:
            print("❌ 沒有銷售記錄")
        else:
            for sale in sales:
                print(f'ID: {sale[0]}, 客戶: {sale[1]}, RMB: {sale[2]}, TWD: {sale[3]}, 時間: {sale[4]}')
        
        # 檢查LedgerEntry中的PROFIT_EARNED記錄
        cursor.execute('''
            SELECT id, entry_type, amount, description, created_at 
            FROM ledger_entry 
            WHERE entry_type = "PROFIT_EARNED" 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        profit_entries = cursor.fetchall()
        
        print('\n=== PROFIT_EARNED 記錄 ===')
        if not profit_entries:
            print("❌ 沒有PROFIT_EARNED記錄")
        else:
            for entry in profit_entries:
                print(f'ID: {entry[0]}, 類型: {entry[1]}, 金額: {entry[2]}, 描述: {entry[3]}, 時間: {entry[4]}')
        
        # 檢查FIFO庫存分配記錄
        cursor.execute('''
            SELECT id, sales_record_id, allocated_rmb, allocated_cost_twd 
            FROM fifo_sales_allocation 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        allocations = cursor.fetchall()
        
        print('\n=== FIFO分配記錄 ===')
        if not allocations:
            print("❌ 沒有FIFO分配記錄")
        else:
            for alloc in allocations:
                print(f'ID: {alloc[0]}, 銷售ID: {alloc[1]}, 分配RMB: {alloc[2]}, 成本TWD: {alloc[3]}')
        
        # 檢查所有LedgerEntry類型
        cursor.execute('''
            SELECT entry_type, COUNT(*) as count 
            FROM ledger_entry 
            GROUP BY entry_type 
            ORDER BY count DESC
        ''')
        entry_types = cursor.fetchall()
        
        print('\n=== LedgerEntry 類型統計 ===')
        for entry_type in entry_types:
            print(f'{entry_type[0]}: {entry_type[1]} 筆')
            
    except Exception as e:
        print(f"❌ 查詢錯誤: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_sales_profit()
