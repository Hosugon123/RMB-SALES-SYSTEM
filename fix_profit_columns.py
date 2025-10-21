#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復利潤欄位問題
確保 ledger_entries 表有正確的利潤欄位
"""

import sqlite3
import os

def check_and_fix_columns():
    """檢查並修復資料庫欄位"""
    db_path = 'instance/sales_system.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 檢查 ledger_entries 表結構...")
        
        # 檢查現有欄位
        cursor.execute('PRAGMA table_info(ledger_entries)')
        columns = cursor.fetchall()
        existing_columns = {col[1] for col in columns}
        
        print(f"📋 現有欄位: {sorted(existing_columns)}")
        
        # 需要添加的利潤欄位
        profit_columns = {
            'profit_before': 'FLOAT',
            'profit_after': 'FLOAT', 
            'profit_change': 'FLOAT'
        }
        
        # 檢查並添加缺失的欄位
        added_columns = []
        for column_name, column_type in profit_columns.items():
            if column_name not in existing_columns:
                print(f"➕ 添加欄位: {column_name}")
                cursor.execute(f'ALTER TABLE ledger_entries ADD COLUMN {column_name} {column_type}')
                added_columns.append(column_name)
            else:
                print(f"✅ 欄位已存在: {column_name}")
        
        # 提交更改
        conn.commit()
        
        if added_columns:
            print(f"✅ 成功添加欄位: {added_columns}")
        else:
            print("✅ 所有利潤欄位都已存在")
        
        # 驗證欄位
        cursor.execute('PRAGMA table_info(ledger_entries)')
        columns = cursor.fetchall()
        updated_columns = {col[1] for col in columns}
        
        print(f"\n📋 更新後的欄位: {sorted(updated_columns)}")
        
        # 檢查利潤相關記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries WHERE entry_type = "PROFIT_WITHDRAW"')
        profit_count = cursor.fetchone()[0]
        print(f"\n💰 利潤提款記錄數量: {profit_count}")
        
        if profit_count > 0:
            cursor.execute('''
                SELECT id, amount, description, entry_date,
                       profit_before, profit_after, profit_change
                FROM ledger_entries 
                WHERE entry_type = "PROFIT_WITHDRAW"
                ORDER BY entry_date DESC
                LIMIT 3
            ''')
            records = cursor.fetchall()
            print(f"\n📋 最近的利潤提款記錄:")
            for record in records:
                print(f"  ID: {record[0]}, 金額: {record[1]}, 描述: {record[2]}")
                print(f"    日期: {record[3]}")
                print(f"    利潤前: {record[4]}, 利潤後: {record[5]}, 利潤變動: {record[6]}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    print("🚀 開始修復利潤欄位問題...")
    print("=" * 50)
    
    if check_and_fix_columns():
        print("\n✅ 修復完成！")
        print("\n💡 建議:")
        print("  1. 重新啟動應用程式")
        print("  2. 檢查利潤管理頁面是否正常顯示")
        print("  3. 如果仍有問題，可能需要重新執行利潤提款操作")
    else:
        print("\n❌ 修復失敗！")
    
    print("\n🎯 修復腳本執行完成!")

if __name__ == '__main__':
    main()
