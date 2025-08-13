#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查應收帳款數據腳本
"""

import sqlite3
import os

def check_ar_data():
    """檢查應收帳款數據"""
    
    # 嘗試多個可能的數據庫路徑
    db_paths = [
        'sales_system_v4.db',
        'instance/sales_system_v4.db',
        '../instance/sales_system_v4.db',
        '../../instance/sales_system_v4.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 找不到數據庫文件")
        return False
    
    print(f"✅ 找到數據庫: {db_path}")
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 檢查應收帳款相關數據...")
        
        # 1. 檢查customers表
        print("\n1. 檢查customers表:")
        cursor.execute("SELECT id, name, is_active, total_receivables_twd FROM customers")
        customers = cursor.fetchall()
        
        if customers:
            for customer in customers:
                print(f"   - ID: {customer[0]}, 名稱: {customer[1]}, 啟用: {customer[2]}, 應收帳款: NT$ {customer[3]:,.2f}")
        else:
            print("   - 沒有客戶記錄")
        
        # 2. 檢查sales_records表
        print("\n2. 檢查sales_records表:")
        cursor.execute("SELECT id, customer_id, twd_amount, rmb_amount, created_at FROM sales_records")
        sales = cursor.fetchall()
        
        if sales:
            for sale in sales:
                print(f"   - ID: {sale[0]}, 客戶ID: {sale[1]}, TWD金額: {sale[2]:,.2f}, RMB金額: {sale[3]:,.2f}, 創建時間: {sale[4]}")
        else:
            print("   - 沒有銷售記錄")
        
        # 3. 檢查ledger_entries表中的銷帳記錄
        print("\n3. 檢查銷帳記錄:")
        cursor.execute("SELECT id, entry_type, amount, description, entry_date FROM ledger_entries WHERE entry_type = 'SETTLEMENT'")
        settlements = cursor.fetchall()
        
        if settlements:
            for settlement in settlements:
                print(f"   - ID: {settlement[0]}, 類型: {settlement[1]}, 金額: {settlement[2]:,.2f}, 描述: {settlement[3]}, 日期: {settlement[4]}")
        else:
            print("   - 沒有銷帳記錄")
        
        # 4. 計算理論應收帳款
        print("\n4. 計算理論應收帳款:")
        cursor.execute("SELECT SUM(twd_amount) FROM sales_records")
        total_sales = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM ledger_entries WHERE entry_type = 'SETTLEMENT'")
        total_settlements = cursor.fetchone()[0] or 0
        
        theoretical_ar = total_sales - total_settlements
        print(f"   - 總銷售金額: NT$ {total_sales:,.2f}")
        print(f"   - 總銷帳金額: NT$ {total_settlements:,.2f}")
        print(f"   - 理論應收帳款: NT$ {theoretical_ar:,.2f}")
        
        # 5. 檢查實際應收帳款總和
        print("\n5. 檢查實際應收帳款總和:")
        cursor.execute("SELECT SUM(total_receivables_twd) FROM customers WHERE is_active = 1")
        actual_ar = cursor.fetchone()[0] or 0
        print(f"   - 實際應收帳款總和: NT$ {actual_ar:,.2f}")
        
        # 6. 檢查差異
        print("\n6. 檢查差異:")
        difference = theoretical_ar - actual_ar
        print(f"   - 差異: NT$ {difference:,.2f}")
        if abs(difference) > 0.01:  # 允許0.01的浮點數誤差
            print("   ⚠️  理論值和實際值不一致！")
        else:
            print("   ✅ 理論值和實際值一致")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 數據庫操作錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 發生未知錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🔍 開始檢查應收帳款數據...")
    print("=" * 50)
    
    success = check_ar_data()
    
    print("=" * 50)
    if success:
        print("🎯 檢查完成！")
    else:
        print("💥 檢查失敗！")
    
    input("\n按 Enter 鍵退出...")


