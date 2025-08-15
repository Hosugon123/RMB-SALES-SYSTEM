#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帳戶餘額計算調試腳本
用於診斷餘額計算問題
"""

import sqlite3
import json
from datetime import datetime

def debug_account_balances():
    """調試帳戶餘額計算"""
    
    # 連接數據庫
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("🔍 開始調試帳戶餘額計算...")
    print("=" * 60)
    
    # 1. 檢查所有帳戶的當前餘額
    print("\n📊 1. 檢查所有帳戶的當前餘額:")
    cursor.execute("""
        SELECT 
            h.name as holder_name,
            ca.name as account_name,
            ca.currency,
            ca.balance as db_balance,
            ca.id as account_id
        FROM cash_account ca
        JOIN holder h ON ca.holder_id = h.id
        WHERE ca.is_active = 1
        ORDER BY h.name, ca.currency
    """)
    
    accounts = cursor.fetchall()
    print(f"{'持有人':<10} {'帳戶名':<15} {'幣種':<5} {'數據庫餘額':<15} {'帳戶ID':<5}")
    print("-" * 60)
    
    total_twd_db = 0
    total_rmb_db = 0
    
    for acc in accounts:
        holder_name, account_name, currency, db_balance, account_id = acc
        print(f"{holder_name:<10} {account_name:<15} {currency:<5} {db_balance:<15} {account_id:<5}")
        
        if currency == 'TWD':
            total_twd_db += db_balance
        elif currency == 'RMB':
            total_rmb_db += db_balance
    
    print("-" * 60)
    print(f"數據庫總台幣餘額: {total_twd_db:,.2f}")
    print(f"數據庫總人民幣餘額: {total_rmb_db:,.2f}")
    
    # 2. 檢查所有交易記錄
    print("\n📈 2. 檢查所有交易記錄:")
    
    # 買入記錄
    cursor.execute("""
        SELECT 
            p.purchase_date,
            p.twd_cost,
            p.rmb_amount,
            pa.name as payment_account,
            da.name as deposit_account,
            pa.id as payment_account_id,
            da.id as deposit_account_id
        FROM purchase_record p
        JOIN cash_account pa ON p.payment_account_id = pa.id
        JOIN cash_account da ON p.deposit_account_id = da.id
        ORDER BY p.purchase_date
    """)
    
    purchases = cursor.fetchall()
    print(f"\n🛒 買入記錄 ({len(purchases)} 筆):")
    print(f"{'日期':<12} {'TWD成本':<12} {'RMB數量':<12} {'付款帳戶':<15} {'收款帳戶':<15}")
    print("-" * 70)
    
    total_twd_spent = 0
    total_rmb_gained = 0
    
    for p in purchases:
        date, twd_cost, rmb_amount, payment_account, deposit_account, pa_id, da_id = p
        print(f"{date:<12} {twd_cost:<12,.2f} {rmb_amount:<12,.2f} {payment_account:<15} {deposit_account:<15}")
        total_twd_spent += twd_cost
        total_rmb_gained += rmb_amount
    
    print("-" * 70)
    print(f"總TWD支出: {total_twd_spent:,.2f}")
    print(f"總RMB獲得: {total_rmb_gained:,.2f}")
    
    # 銷售記錄
    cursor.execute("""
        SELECT 
            s.created_at,
            s.twd_amount,
            s.rmb_amount,
            c.name as customer_name
        FROM sales_record s
        JOIN customer c ON s.customer_id = c.id
        ORDER BY s.created_at
    """)
    
    sales = cursor.fetchall()
    print(f"\n💰 銷售記錄 ({len(sales)} 筆):")
    print(f"{'日期':<12} {'TWD金額':<12} {'RMB數量':<12} {'客戶':<15}")
    print("-" * 60)
    
    total_twd_gained = 0
    total_rmb_sold = 0
    
    for s in sales:
        date, twd_amount, rmb_amount, customer_name = s
        print(f"{date:<12} {twd_amount:<12,.2f} {rmb_amount:<12,.2f} {customer_name:<15}")
        total_twd_gained += twd_amount
        total_rmb_sold += rmb_amount
    
    print("-" * 60)
    print(f"總TWD獲得: {total_twd_gained:,.2f}")
    print(f"總RMB售出: {total_rmb_sold:,.2f}")
    
    # 記帳記錄
    cursor.execute("""
        SELECT 
            le.entry_date,
            le.entry_type,
            le.amount,
            ca.name as account_name,
            ca.currency
        FROM ledger_entry le
        JOIN cash_account ca ON le.account_id = ca.id
        WHERE le.entry_type NOT IN ('BUY_IN_DEBIT', 'BUY_IN_CREDIT')
        ORDER BY le.entry_date
    """)
    
    ledger_entries = cursor.fetchall()
    print(f"\n📝 記帳記錄 ({len(ledger_entries)} 筆):")
    print(f"{'日期':<12} {'類型':<15} {'金額':<12} {'帳戶':<15} {'幣種':<5}")
    print("-" * 65)
    
    for le in ledger_entries:
        date, entry_type, amount, account_name, currency = le
        print(f"{date:<12} {entry_type:<15} {amount:<12,.2f} {account_name:<15} {currency:<5}")
    
    # 現金日誌
    cursor.execute("""
        SELECT 
            cl.time,
            cl.type,
            cl.amount
        FROM cash_log cl
        WHERE cl.type != 'BUY_IN'
        ORDER BY cl.time
    """)
    
    cash_logs = cursor.fetchall()
    print(f"\n💳 現金日誌 ({len(cash_logs)} 筆):")
    print(f"{'時間':<12} {'類型':<15} {'金額':<12}")
    print("-" * 45)
    
    for cl in cash_logs:
        time, log_type, amount = cl
        print(f"{time:<12} {log_type:<15} {amount:<12,.2f}")
    
    # 3. 計算理論餘額
    print("\n🧮 3. 計算理論餘額:")
    
    # 假設初始餘額為0，計算理論餘額
    theoretical_twd = total_twd_gained - total_twd_spent
    theoretical_rmb = total_rmb_gained - total_rmb_sold
    
    print(f"理論TWD餘額: {theoretical_twd:,.2f}")
    print(f"理論RMB餘額: {theoretical_rmb:,.2f}")
    print(f"數據庫TWD餘額: {total_twd_db:,.2f}")
    print(f"數據庫RMB餘額: {total_rmb_db:,.2f}")
    
    # 4. 差異分析
    print("\n⚠️ 4. 差異分析:")
    twd_diff = theoretical_twd - total_twd_db
    rmb_diff = theoretical_rmb - total_rmb_db
    
    print(f"TWD差異: {twd_diff:,.2f}")
    print(f"RMB差異: {rmb_diff:,.2f}")
    
    if abs(twd_diff) > 0.01:
        print(f"❌ TWD餘額計算有問題！差異: {twd_diff:,.2f}")
    else:
        print("✅ TWD餘額計算正確")
    
    if abs(rmb_diff) > 0.01:
        print(f"❌ RMB餘額計算有問題！差異: {rmb_diff:,.2f}")
    else:
        print("✅ RMB餘額計算正確")
    
    # 5. 檢查是否有重複記錄
    print("\n🔍 5. 檢查重複記錄:")
    
    # 檢查重複的買入記錄
    cursor.execute("""
        SELECT COUNT(*) as count, 
               p.purchase_date, 
               p.twd_cost, 
               p.rmb_amount,
               pa.name as payment_account,
               da.name as deposit_account
        FROM purchase_record p
        JOIN cash_account pa ON p.payment_account_id = pa.id
        JOIN cash_account da ON p.deposit_account_id = da.id
        GROUP BY p.purchase_date, p.twd_cost, p.rmb_amount, p.payment_account_id, p.deposit_account_id
        HAVING COUNT(*) > 1
    """)
    
    duplicate_purchases = cursor.fetchall()
    if duplicate_purchases:
        print(f"⚠️ 發現 {len(duplicate_purchases)} 組重複的買入記錄:")
        for dup in duplicate_purchases:
            count, date, twd_cost, rmb_amount, payment_account, deposit_account = dup
            print(f"   {date} - TWD:{twd_cost:,.2f} RMB:{rmb_amount:,.2f} 付款:{payment_account} 收款:{deposit_account} (重複{count}次)")
    else:
        print("✅ 沒有重複的買入記錄")
    
    # 檢查重複的銷售記錄
    cursor.execute("""
        SELECT COUNT(*) as count, 
               s.created_at, 
               s.twd_amount, 
               s.rmb_amount,
               c.name as customer_name
        FROM sales_record s
        JOIN customer c ON s.customer_id = c.id
        GROUP BY s.created_at, s.twd_amount, s.rmb_amount, s.customer_id
        HAVING COUNT(*) > 1
    """)
    
    duplicate_sales = cursor.fetchall()
    if duplicate_sales:
        print(f"⚠️ 發現 {len(duplicate_sales)} 組重複的銷售記錄:")
        for dup in duplicate_sales:
            count, date, twd_amount, rmb_amount, customer_name = dup
            print(f"   {date} - TWD:{twd_amount:,.2f} RMB:{rmb_amount:,.2f} 客戶:{customer_name} (重複{count}次)")
    else:
        print("✅ 沒有重複的銷售記錄")
    
    conn.close()
    print("\n" + "=" * 60)
    print("🔍 調試完成！")

if __name__ == "__main__":
    debug_account_balances()
