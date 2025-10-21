#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def test_transfer_records():
    """測試內部轉帳記錄的帳戶餘額變化"""
    db_path = 'instance/sales_system_v4.db'
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=== 測試內部轉帳記錄 ===")
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 檢查TRANSFER記錄
        cursor.execute('''
            SELECT id, entry_type, amount, description, account_id, entry_date
            FROM ledger_entries 
            WHERE entry_type IN ('TRANSFER_IN', 'TRANSFER_OUT')
            ORDER BY entry_date DESC
            LIMIT 10
        ''')
        transfer_entries = cursor.fetchall()
        
        print(f"找到 {len(transfer_entries)} 筆轉帳記錄:")
        for entry in transfer_entries:
            entry_id, entry_type, amount, description, account_id, entry_date = entry
            print(f"  ID {entry_id}: {entry_type} - {amount} - {description} ({entry_date})")
        
        print()
        
        # 2. 檢查對應的帳戶餘額
        for entry in transfer_entries:
            entry_id, entry_type, amount, description, account_id, entry_date = entry
            
            if account_id:
                cursor.execute('''
                    SELECT name, balance, currency
                    FROM cash_accounts 
                    WHERE id = ?
                ''', (account_id,))
                account = cursor.fetchone()
                
                if account:
                    account_name, balance, currency = account
                    print(f"帳戶 {account_name} ({currency}):")
                    print(f"  當前餘額: {balance:.2f}")
                    
                    # 計算變動前後的餘額
                    if entry_type == "TRANSFER_IN":
                        balance_before = balance - amount
                        balance_after = balance
                        change = amount
                        print(f"  變動前: {balance_before:.2f}")
                        print(f"  變動: +{change:.2f}")
                        print(f"  變動後: {balance_after:.2f}")
                    elif entry_type == "TRANSFER_OUT":
                        balance_before = balance + amount
                        balance_after = balance
                        change = -amount
                        print(f"  變動前: {balance_before:.2f}")
                        print(f"  變動: {change:.2f}")
                        print(f"  變動後: {balance_after:.2f}")
                    
                    print()
        
        # 3. 檢查其他類型的記錄
        cursor.execute('''
            SELECT entry_type, COUNT(*) as count
            FROM ledger_entries 
            GROUP BY entry_type
            ORDER BY count DESC
        ''')
        entry_types = cursor.fetchall()
        
        print("所有記錄類型統計:")
        for entry_type, count in entry_types:
            print(f"  {entry_type}: {count} 筆")
        
        print()
        print("=== 測試完成 ===")
        print("修正後，所有交易記錄都應該包含帳戶餘額的前後變化信息")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_transfer_records()
