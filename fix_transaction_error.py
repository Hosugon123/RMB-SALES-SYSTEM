#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復事務衝突問題
解決 "A transaction is already begun on this Session" 錯誤
"""

import sqlite3
import os

def fix_database_columns_safely():
    """安全地修復資料庫欄位，避免事務衝突"""
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
        
        # 需要添加的欄位
        required_columns = {
            'profit_before': 'FLOAT',
            'profit_after': 'FLOAT', 
            'profit_change': 'FLOAT',
            'from_account_id': 'INTEGER',
            'to_account_id': 'INTEGER'
        }
        
        # 檢查並添加缺失的欄位
        added_columns = []
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                print(f"➕ 添加欄位: {column_name}")
                try:
                    cursor.execute(f'ALTER TABLE ledger_entries ADD COLUMN {column_name} {column_type}')
                    added_columns.append(column_name)
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️ 欄位 {column_name} 可能已存在，跳過")
                    else:
                        print(f"❌ 添加欄位 {column_name} 失敗: {e}")
            else:
                print(f"✅ 欄位已存在: {column_name}")
        
        # 提交更改
        conn.commit()
        
        if added_columns:
            print(f"✅ 成功添加欄位: {added_columns}")
        else:
            print("✅ 所有必要欄位都已存在")
        
        # 驗證欄位
        cursor.execute('PRAGMA table_info(ledger_entries)')
        columns = cursor.fetchall()
        updated_columns = {col[1] for col in columns}
        
        print(f"\n📋 更新後的欄位: {sorted(updated_columns)}")
        
        # 檢查記錄數量
        cursor.execute('SELECT COUNT(*) FROM ledger_entries')
        total_count = cursor.fetchone()[0]
        print(f"\n📊 總記錄數: {total_count}")
        
        # 檢查利潤提款記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries WHERE entry_type = "PROFIT_WITHDRAW"')
        profit_count = cursor.fetchone()[0]
        print(f"💰 利潤提款記錄: {profit_count}")
        
        # 檢查轉帳記錄
        cursor.execute('SELECT COUNT(*) FROM ledger_entries WHERE from_account_id IS NOT NULL OR to_account_id IS NOT NULL')
        transfer_count = cursor.fetchone()[0]
        print(f"🔄 轉帳記錄: {transfer_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def test_database_queries():
    """測試資料庫查詢是否正常"""
    db_path = 'instance/sales_system.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🧪 測試資料庫查詢...")
        
        # 測試基本查詢
        cursor.execute('SELECT COUNT(*) FROM ledger_entries')
        count = cursor.fetchone()[0]
        print(f"✅ 基本查詢正常: {count} 筆記錄")
        
        # 測試包含新欄位的查詢
        cursor.execute('''
            SELECT id, entry_type, amount, description, 
                   profit_before, profit_after, profit_change,
                   from_account_id, to_account_id
            FROM ledger_entries 
            ORDER BY entry_date DESC 
            LIMIT 5
        ''')
        records = cursor.fetchall()
        print(f"✅ 包含新欄位的查詢正常: {len(records)} 筆記錄")
        
        # 測試利潤提款查詢
        cursor.execute('''
            SELECT COUNT(*) FROM ledger_entries 
            WHERE entry_type = "PROFIT_WITHDRAW"
        ''')
        profit_count = cursor.fetchone()[0]
        print(f"✅ 利潤提款查詢正常: {profit_count} 筆記錄")
        
        return True
        
    except Exception as e:
        print(f"❌ 查詢測試失敗: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    print("🚀 開始修復事務衝突問題...")
    print("=" * 60)
    
    # 1. 修復資料庫欄位
    if fix_database_columns_safely():
        print("\n✅ 資料庫欄位修復完成！")
        
        # 2. 測試資料庫查詢
        if test_database_queries():
            print("\n✅ 資料庫查詢測試通過！")
            
            print("\n💡 建議:")
            print("  1. 重新啟動應用程式")
            print("  2. 檢查現金管理頁面是否正常載入")
            print("  3. 檢查利潤管理頁面是否正常顯示")
            print("  4. 如果仍有問題，請檢查應用程式日誌")
        else:
            print("\n⚠️ 資料庫查詢測試失敗，請檢查資料庫狀態")
    else:
        print("\n❌ 資料庫欄位修復失敗！")
        print("請手動檢查資料庫連接和權限")
    
    print("\n🎯 修復腳本執行完成!")

if __name__ == '__main__':
    main()
