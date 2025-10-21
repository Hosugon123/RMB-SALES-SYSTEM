#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
利潤記錄診斷腳本
檢查利潤更動紀錄不顯示的問題
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_database_structure():
    """檢查資料庫結構"""
    print("🔍 檢查資料庫結構...")
    
    db_path = 'instance/sales_system.db'
    if not os.path.exists(db_path):
        print(f"❌ 資料庫不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 檢查 LedgerEntry 表結構
        cursor.execute('PRAGMA table_info(ledger_entries)')
        columns = cursor.fetchall()
        print("\n📋 LedgerEntry 表結構:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} {'(NOT NULL)' if col[3] else ''}")
        
        # 檢查是否有利潤相關欄位
        profit_columns = [col[1] for col in columns if 'profit' in col[1].lower()]
        print(f"\n💰 利潤相關欄位: {profit_columns}")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查表結構失敗: {e}")
        return False
    finally:
        conn.close()

def check_profit_records():
    """檢查利潤記錄"""
    print("\n🔍 檢查利潤記錄...")
    
    db_path = 'instance/sales_system.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 檢查所有 LedgerEntry 記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries')
        total_count = cursor.fetchone()[0]
        print(f"📊 總記錄數: {total_count}")
        
        # 檢查利潤提款記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries WHERE entry_type = "PROFIT_WITHDRAW"')
        profit_withdraw_count = cursor.fetchone()[0]
        print(f"💰 利潤提款記錄: {profit_withdraw_count}")
        
        # 檢查利潤相關記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries WHERE description LIKE "%利潤%"')
        profit_related_count = cursor.fetchone()[0]
        print(f"📝 利潤相關記錄: {profit_related_count}")
        
        # 檢查所有 entry_type
        cursor.execute('SELECT DISTINCT entry_type FROM ledger_entries')
        entry_types = cursor.fetchall()
        print(f"\n📋 所有記錄類型: {[t[0] for t in entry_types]}")
        
        # 檢查最近的記錄
        cursor.execute('''
            SELECT id, entry_type, amount, description, entry_date 
            FROM ledger_entries 
            ORDER BY entry_date DESC 
            LIMIT 10
        ''')
        recent_records = cursor.fetchall()
        print(f"\n📅 最近10筆記錄:")
        for record in recent_records:
            print(f"  ID: {record[0]}, 類型: {record[1]}, 金額: {record[2]}, 描述: {record[3]}, 日期: {record[4]}")
        
        # 檢查利潤提款記錄詳情
        if profit_withdraw_count > 0:
            cursor.execute('''
                SELECT id, amount, description, entry_date, 
                       profit_before, profit_after, profit_change
                FROM ledger_entries 
                WHERE entry_type = "PROFIT_WITHDRAW"
                ORDER BY entry_date DESC
            ''')
            profit_records = cursor.fetchall()
            print(f"\n💰 利潤提款記錄詳情:")
            for record in profit_records:
                print(f"  ID: {record[0]}, 金額: {record[1]}, 描述: {record[2]}")
                print(f"    日期: {record[3]}")
                print(f"    利潤前: {record[4]}, 利潤後: {record[5]}, 利潤變動: {record[6]}")
                print()
        
        return profit_withdraw_count > 0
        
    except Exception as e:
        print(f"❌ 檢查記錄失敗: {e}")
        return False
    finally:
        conn.close()

def check_sales_records():
    """檢查銷售記錄"""
    print("\n🔍 檢查銷售記錄...")
    
    db_path = 'instance/sales_system.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 檢查銷售記錄
        cursor.execute('SELECT COUNT(*) FROM sales_records')
        sales_count = cursor.fetchone()[0]
        print(f"📊 銷售記錄數: {sales_count}")
        
        if sales_count > 0:
            # 檢查最近的銷售記錄
            cursor.execute('''
                SELECT id, customer_name, total_amount, profit_twd, created_at
                FROM sales_records 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent_sales = cursor.fetchall()
            print(f"\n📅 最近5筆銷售記錄:")
            for sale in recent_sales:
                print(f"  ID: {sale[0]}, 客戶: {sale[1]}, 金額: {sale[2]}, 利潤: {sale[3]}, 日期: {sale[4]}")
        
        return sales_count > 0
        
    except Exception as e:
        print(f"❌ 檢查銷售記錄失敗: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    print("🚀 利潤記錄診斷開始...")
    print("=" * 50)
    
    # 1. 檢查資料庫結構
    if not check_database_structure():
        print("❌ 資料庫結構檢查失敗")
        return
    
    # 2. 檢查利潤記錄
    has_profit_records = check_profit_records()
    
    # 3. 檢查銷售記錄
    has_sales_records = check_sales_records()
    
    print("\n" + "=" * 50)
    print("📋 診斷結果:")
    print(f"  ✅ 資料庫結構: 正常")
    print(f"  {'✅' if has_profit_records else '❌'} 利潤記錄: {'有記錄' if has_profit_records else '無記錄'}")
    print(f"  {'✅' if has_sales_records else '❌'} 銷售記錄: {'有記錄' if has_sales_records else '無記錄'}")
    
    if not has_profit_records:
        print("\n💡 建議:")
        print("  1. 檢查是否有進行過利潤提款操作")
        print("  2. 檢查資料庫是否被清空過")
        print("  3. 檢查利潤提款記錄是否正確保存")
    
    print("\n🎯 診斷完成!")

if __name__ == '__main__':
    main()
