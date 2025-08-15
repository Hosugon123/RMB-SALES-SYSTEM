#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急診斷：帳戶餘額與提款邏輯不一致問題
"""

import sqlite3
import os

def check_balance_discrepancy():
    """檢查帳戶餘額與提款邏輯的不一致問題"""
    
    # 檢查數據庫文件位置
    db_paths = [
        'database.db',
        'instance/database.db',
        'instance/rmb_sales_system.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 找不到數據庫文件！")
        return
    
    print(f"🔍 使用數據庫: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 1. 檢查所有帳戶的當前餘額:")
        cursor.execute("""
            SELECT 
                h.name as holder_name,
                ca.name as account_name,
                ca.currency,
                ca.balance as db_balance,
                ca.id as account_id,
                ca.is_active
            FROM cash_account ca
            JOIN holder h ON ca.holder_id = h.id
            ORDER BY h.name, ca.currency
        """)
        
        accounts = cursor.fetchall()
        print(f"{'持有人':<8} {'帳戶名':<12} {'幣種':<5} {'數據庫餘額':<15} {'狀態':<8}")
        print("-" * 60)
        
        total_twd_db = 0
        total_rmb_db = 0
        active_twd_db = 0
        active_rmb_db = 0
        
        for acc in accounts:
            holder_name, account_name, currency, db_balance, account_id, is_active = acc
            status = "啟用" if is_active else "停用"
            print(f"{holder_name:<8} {account_name:<12} {currency:<5} {db_balance:<15,.2f} {status:<8}")
            
            if currency == 'TWD':
                total_twd_db += db_balance
                if is_active:
                    active_twd_db += db_balance
            elif currency == 'RMB':
                total_rmb_db += db_balance
                if is_active:
                    active_rmb_db += db_balance
        
        print("-" * 60)
        print(f"所有TWD帳戶餘額: {total_twd_db:,.2f}")
        print(f"啟用TWD帳戶餘額: {active_twd_db:,.2f}")
        print(f"所有RMB帳戶餘額: {total_rmb_db:,.2f}")
        print(f"啟用RMB帳戶餘額: {active_rmb_db:,.2f}")
        
        # 檢查提款相關的邏輯
        print("\n💳 2. 檢查提款相關邏輯:")
        
        # 檢查是否有提款限制
        cursor.execute("""
            SELECT name, value FROM system_config 
            WHERE name LIKE '%withdraw%' OR name LIKE '%提款%' OR name LIKE '%餘額%'
        """)
        
        withdraw_configs = cursor.fetchall()
        if withdraw_configs:
            print("提款相關配置:")
            for name, value in withdraw_configs:
                print(f"  {name}: {value}")
        else:
            print("沒有找到提款相關配置")
        
        # 檢查最近的提款記錄
        cursor.execute("""
            SELECT 
                cl.time,
                cl.type,
                cl.amount,
                cl.description
            FROM cash_log cl
            WHERE cl.type IN ('WITHDRAW', '提款', '轉出')
            ORDER BY cl.time DESC
            LIMIT 10
        """)
        
        withdraw_logs = cursor.fetchall()
        if withdraw_logs:
            print(f"\n最近提款記錄 ({len(withdraw_logs)} 筆):")
            for log in withdraw_logs:
                time, log_type, amount, description = log
                print(f"  {time} - {log_type}: {amount:,.2f} - {description}")
        else:
            print("\n沒有找到提款記錄")
        
        # 檢查帳戶餘額變更歷史
        print("\n📈 3. 檢查帳戶餘額變更歷史:")
        cursor.execute("""
            SELECT 
                ca.name,
                ca.currency,
                ca.balance,
                ca.created_at,
                ca.updated_at
            FROM cash_account ca
            WHERE ca.currency = 'TWD'
            ORDER BY ca.balance DESC
        """)
        
        twd_accounts = cursor.fetchall()
        print("TWD帳戶餘額詳情:")
        for acc in twd_accounts:
            name, currency, balance, created_at, updated_at = acc
            print(f"  {name}: {balance:,.2f} (創建: {created_at}, 更新: {updated_at})")
        
        # 檢查是否有隱藏的餘額限制
        print("\n🔒 4. 檢查隱藏的餘額限制:")
        
        # 檢查是否有凍結的帳戶
        cursor.execute("""
            SELECT 
                ca.name,
                ca.currency,
                ca.balance,
                ca.is_active,
                ca.is_frozen
            FROM cash_account ca
            WHERE ca.currency = 'TWD' AND ca.is_active = 1
        """)
        
        active_twd_accounts = cursor.fetchall()
        print("啟用的TWD帳戶:")
        for acc in active_twd_accounts:
            name, currency, balance, is_active, is_frozen = acc
            frozen_status = "凍結" if is_frozen else "正常"
            print(f"  {name}: {balance:,.2f} - 狀態: {frozen_status}")
        
        # 檢查總資產計算邏輯
        print("\n🧮 5. 總資產計算邏輯檢查:")
        
        # 檢查現金管理頁面的總資產計算
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN ca.currency = 'TWD' THEN ca.balance ELSE 0 END) as total_twd,
                SUM(CASE WHEN ca.currency = 'RMB' THEN ca.balance ELSE 0 END) as total_rmb
            FROM cash_account ca
            WHERE ca.is_active = 1
        """)
        
        total_assets = cursor.fetchone()
        if total_assets:
            total_twd, total_rmb = total_assets
            print(f"現金管理頁面計算的總資產:")
            print(f"  總TWD: {total_twd:,.2f}")
            print(f"  總RMB: {total_rmb:,.2f}")
            
            # 與實際帳戶餘額比較
            print(f"\n差異分析:")
            print(f"  顯示的總TWD: 273,148.00")
            print(f"  實際帳戶TWD: {total_twd:,.2f}")
            print(f"  差異: {273148 - total_twd:,.2f}")
            
            if abs(273148 - total_twd) > 0.01:
                print(f"  ❌ 總資產計算有重大差異！")
            else:
                print(f"  ✅ 總資產計算正確")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_balance_discrepancy()
