#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫欄位修復腳本
修復 ledger_entries 表缺少的欄位問題
"""

import sqlite3
import os
import sys

def check_and_fix_ledger_columns():
    """檢查並修復 ledger_entries 表的欄位"""
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
                cursor.execute(f'ALTER TABLE ledger_entries ADD COLUMN {column_name} {column_type}')
                added_columns.append(column_name)
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

def test_api_endpoints():
    """測試API端點是否正常工作"""
    print("\n🧪 測試API端點...")
    
    try:
        import requests
        
        base_url = "https://rmb-sales-system-test1.onrender.com"
        
        # 測試交易記錄API
        print("📡 測試交易記錄API...")
        response = requests.get(f"{base_url}/api/cash_management/transactions?page=1&per_page=5", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                transactions = data.get("data", {}).get("transactions", [])
                print(f"✅ 交易記錄API正常，返回 {len(transactions)} 筆記錄")
            else:
                print(f"⚠️ 交易記錄API返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ 交易記錄API HTTP錯誤: {response.status_code}")
        
        # 測試利潤歷史API
        print("📡 測試利潤歷史API...")
        response = requests.get(f"{base_url}/api/profit/history?page=1&per_page=5", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                transactions = data.get("data", {}).get("transactions", [])
                print(f"✅ 利潤歷史API正常，返回 {len(transactions)} 筆記錄")
            else:
                print(f"⚠️ 利潤歷史API返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ 利潤歷史API HTTP錯誤: {response.status_code}")
            
    except ImportError:
        print("⚠️ 無法測試API端點（缺少 requests 模組）")
    except Exception as e:
        print(f"❌ API測試失敗: {e}")

def main():
    """主函數"""
    print("🚀 開始修復資料庫欄位問題...")
    print("=" * 60)
    
    # 1. 修復資料庫欄位
    if check_and_fix_ledger_columns():
        print("\n✅ 資料庫欄位修復完成！")
        
        # 2. 測試API端點
        test_api_endpoints()
        
        print("\n💡 建議:")
        print("  1. 重新啟動應用程式")
        print("  2. 檢查現金管理頁面是否正常載入")
        print("  3. 檢查利潤管理頁面是否正常顯示")
        print("  4. 如果仍有問題，請檢查應用程式日誌")
    else:
        print("\n❌ 資料庫欄位修復失敗！")
        print("請手動檢查資料庫連接和權限")
    
    print("\n🎯 修復腳本執行完成!")

if __name__ == '__main__':
    main()
