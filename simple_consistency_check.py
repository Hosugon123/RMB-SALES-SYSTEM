#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的帳戶數據和庫存數據一致性檢查
"""

import sqlite3
import os

def check_consistency():
    """檢查帳戶餘額和庫存數據的一致性"""
    print("🔍 開始檢查帳戶數據和庫存數據的一致性...")
    
    # 檢查數據庫文件是否存在
    db_path = "instance/sales_system_v4.db"
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 獲取所有RMB帳戶的總餘額
        cursor.execute("""
            SELECT SUM(balance) 
            FROM cash_accounts 
            WHERE currency = 'RMB' AND is_active = 1
        """)
        total_account_rmb = cursor.fetchone()[0] or 0
        print(f"📊 帳戶總RMB餘額: {total_account_rmb:,.2f}")
        
        # 2. 獲取FIFO庫存的總剩餘RMB
        cursor.execute("""
            SELECT SUM(remaining_rmb) 
            FROM fifo_inventory
        """)
        total_inventory_rmb = cursor.fetchone()[0] or 0
        print(f"📦 FIFO庫存總剩餘RMB: {total_inventory_rmb:,.2f}")
        
        # 3. 計算差異
        difference = total_account_rmb - total_inventory_rmb
        print(f"⚠️  差異: {difference:,.2f}")
        
        if abs(difference) > 0.01:  # 允許0.01的浮點數誤差
            print("❌ 帳戶數據和庫存數據不一致！")
            
                    # 4. 詳細分析每個帳戶
        print("\n📋 詳細帳戶分析:")
        cursor.execute("""
            SELECT ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'RMB' AND ca.is_active = 1
            ORDER BY ca.balance DESC
        """)
            accounts = cursor.fetchall()
            for acc in accounts:
                print(f"  - {acc[0]} ({acc[2]}): {acc[1]:,.2f} RMB")
            
                    # 5. 詳細分析庫存
        print("\n📦 詳細庫存分析:")
        cursor.execute("""
            SELECT fi.id, fi.remaining_rmb, pr.rmb_amount, pr.exchange_rate
            FROM fifo_inventory fi
            LEFT JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            ORDER BY fi.remaining_rmb DESC
        """)
            inventory = cursor.fetchall()
            for inv in inventory:
                print(f"  - 批次 {inv[0]}: {inv[1]:,.2f} RMB (原始: {inv[2]:,.2f}, 匯率: {inv[3]:.4f})")
            
                    # 6. 檢查是否有銷售分配記錄
        cursor.execute("SELECT COUNT(*) FROM fifo_sales_allocations")
            allocation_count = cursor.fetchone()[0]
            print(f"\n📊 總共有 {allocation_count} 個庫存分配記錄")
            
            return False
        else:
            print("✅ 帳戶數據和庫存數據一致！")
            return True
            
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def suggest_fixes():
    """建議修復方案"""
    print("\n💡 建議的修復方案:")
    print("1. 檢查是否有銷售記錄創建但庫存未正確扣減")
    print("2. 檢查是否有帳戶餘額變更但未記錄在流水中的情況")
    print("3. 檢查是否有手動修改帳戶餘額但未同步庫存的情況")
    print("4. 檢查是否有庫存分配記錄但帳戶餘額未扣減的情況")
    print("5. 檢查是否有庫存記錄與買入記錄不匹配的情況")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 帳戶數據和庫存數據一致性檢查工具")
    print("=" * 60)
    
    # 檢查一致性
    is_consistent = check_consistency()
    
    if not is_consistent:
        # 提供修復建議
        suggest_fixes()
    
    print("\n" + "=" * 60)
    print("✅ 檢查完成")
    print("=" * 60)
