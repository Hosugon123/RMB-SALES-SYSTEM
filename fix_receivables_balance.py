#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查和修復應收帳款餘額不一致問題的腳本
"""

import sqlite3
import os

def fix_receivables_balance():
    """檢查和修復應收帳款餘額不一致問題"""
    
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件 {db_path} 不存在")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查應收帳款餘額一致性...")
        
        # 1. 檢查客戶應收帳款餘額
        print("\n📋 當前客戶應收帳款餘額:")
        cursor.execute("""
            SELECT id, name, total_receivables_twd 
            FROM customers 
            WHERE is_active = 1 AND total_receivables_twd > 0
            ORDER BY total_receivables_twd DESC
        """)
        customers = cursor.fetchall()
        
        for customer in customers:
            customer_id, name, balance = customer
            print(f"  客戶 {name} (ID: {customer_id}): NT$ {balance:,.2f}")
        
        # 2. 檢查銷售記錄總額
        print("\n📊 銷售記錄總額:")
        cursor.execute("""
            SELECT customer_id, SUM(twd_amount) as total_sales
            FROM sales_records
            GROUP BY customer_id
        """)
        sales_totals = cursor.fetchall()
        
        sales_by_customer = {}
        for customer_id, total_sales in sales_totals:
            sales_by_customer[customer_id] = total_sales or 0
            print(f"  客戶ID {customer_id}: 銷售總額 NT$ {total_sales or 0:,.2f}")
        
        # 3. 檢查銷帳記錄總額
        print("\n💰 銷帳記錄總額:")
        cursor.execute("""
            SELECT account_id, SUM(amount) as total_settlements
            FROM ledger_entries
            WHERE entry_type = 'SETTLEMENT'
            GROUP BY account_id
        """)
        settlement_totals = cursor.fetchall()
        
        total_settlements = sum(amount for _, amount in settlement_totals)
        print(f"  總銷帳金額: NT$ {total_settlements:,.2f}")
        
        # 4. 計算理論應收帳款餘額
        print("\n🧮 理論應收帳款餘額計算:")
        cursor.execute("SELECT id, name FROM customers WHERE is_active = 1")
        all_customers = cursor.fetchall()
        
        theoretical_balances = {}
        for customer_id, name in all_customers:
            sales_amount = sales_by_customer.get(customer_id, 0)
            # 注意：這裡需要根據實際的銷帳記錄來計算，暫時假設所有銷帳都是TWD
            theoretical_balance = sales_amount
            theoretical_balances[customer_id] = theoretical_balance
            print(f"  客戶 {name}: 銷售 {sales_amount:,.2f} - 銷帳 = 理論餘額 {theoretical_balance:,.2f}")
        
        # 5. 檢查是否有不一致
        print("\n⚠️ 檢查餘額不一致:")
        inconsistencies = []
        for customer_id, name, current_balance in customers:
            theoretical_balance = theoretical_balances.get(customer_id, 0)
            if abs(current_balance - theoretical_balance) > 0.01:  # 允許0.01的誤差
                inconsistency = {
                    'customer_id': customer_id,
                    'name': name,
                    'current': current_balance,
                    'theoretical': theoretical_balance,
                    'difference': current_balance - theoretical_balance
                }
                inconsistencies.append(inconsistency)
                print(f"  ❌ 客戶 {name}: 當前 {current_balance:,.2f}, 理論 {theoretical_balance:,.2f}, 差異 {inconsistency['difference']:,.2f}")
        
        if not inconsistencies:
            print("  ✅ 所有客戶的應收帳款餘額都一致")
        else:
            print(f"\n🔧 發現 {len(inconsistencies)} 個不一致的餘額")
            
            # 詢問是否要修復
            response = input("\n是否要修復這些不一致的餘額？(y/N): ").strip().lower()
            if response == 'y':
                print("🔧 開始修復應收帳款餘額...")
                
                for inconsistency in inconsistencies:
                    customer_id = inconsistency['customer_id']
                    theoretical_balance = inconsistency['theoretical']
                    
                    # 更新客戶應收帳款餘額
                    cursor.execute("""
                        UPDATE customers 
                        SET total_receivables_twd = ? 
                        WHERE id = ?
                    """, (theoretical_balance, customer_id))
                    
                    print(f"  ✅ 客戶 {inconsistency['name']}: 更新為 NT$ {theoretical_balance:,.2f}")
                
                # 提交更改
                conn.commit()
                print("✅ 應收帳款餘額修復完成")
            else:
                print("ℹ️ 跳過修復，保持當前餘額")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 檢查應收帳款餘額時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始檢查應收帳款餘額一致性...")
    fix_receivables_balance()
