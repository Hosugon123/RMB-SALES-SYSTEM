#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查帳戶餘額與FIFO庫存的一致性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import CashAccount, FIFOInventory, FIFOSalesAllocation, SalesRecord, PurchaseRecord

def check_account_inventory_consistency():
    """檢查帳戶餘額與FIFO庫存的一致性"""
    
    with app.app_context():
        print("🔍 開始檢查帳戶餘額與FIFO庫存的一致性...")
        print("=" * 80)
        
        # 1. 檢查所有RMB帳戶的餘額
        print("\n📊 1. RMB帳戶餘額統計:")
        rmb_accounts = db.session.execute(
            db.select(CashAccount).filter_by(currency="RMB")
        ).scalars().all()
        
        total_rmb_balance = 0
        for acc in rmb_accounts:
            print(f"   {acc.name}: ¥{acc.balance:,.2f}")
            total_rmb_balance += acc.balance
        
        print(f"   總計: ¥{total_rmb_balance:,.2f}")
        
        # 2. 檢查FIFO庫存狀態
        print("\n📦 2. FIFO庫存狀態:")
        fifo_inventories = db.session.execute(
            db.select(FIFOInventory)
        ).scalars().all()
        
        total_fifo_rmb = 0
        for inv in fifo_inventories:
            print(f"   批次 {inv.id}: 原始 ¥{inv.rmb_amount:,.2f}, 剩餘 ¥{inv.remaining_rmb:,.2f}, 已售 ¥{inv.rmb_amount - inv.remaining_rmb:,.2f}")
            total_fifo_rmb += inv.remaining_rmb
        
        print(f"   總計剩餘庫存: ¥{total_fifo_rmb:,.2f}")
        
        # 3. 檢查銷售分配
        print("\n🔄 3. 銷售分配狀態:")
        sales_allocations = db.session.execute(
            db.select(FIFOSalesAllocation)
        ).scalars().all()
        
        total_allocated_rmb = 0
        for alloc in sales_allocations:
            print(f"   分配 {alloc.id}: 銷售記錄 {alloc.sales_record_id}, 分配 ¥{alloc.allocated_rmb:,.2f}")
            total_allocated_rmb += alloc.allocated_rmb
        
        print(f"   總計已分配: ¥{total_allocated_rmb:,.2f}")
        
        # 4. 檢查銷售記錄
        print("\n📋 4. 銷售記錄狀態:")
        sales_records = db.session.execute(
            db.select(SalesRecord)
        ).scalars().all()
        
        total_sales_rmb = 0
        for sale in sales_records:
            print(f"   銷售 {sale.id}: 客戶 {sale.customer.name if sale.customer else 'N/A'}, 金額 ¥{sale.rmb_amount:,.2f}, 帳戶 {sale.rmb_account.name if sale.rmb_account else 'N/A'}")
            total_sales_rmb += sale.rmb_amount
        
        print(f"   總計銷售: ¥{total_sales_rmb:,.2f}")
        
        # 5. 一致性檢查
        print("\n✅ 5. 一致性檢查:")
        
        # 理論上：帳戶餘額 + 已分配庫存 = 原始庫存
        expected_balance = total_fifo_rmb + total_allocated_rmb
        actual_balance = total_rmb_balance
        
        print(f"   帳戶餘額: ¥{actual_balance:,.2f}")
        print(f"   庫存剩餘: ¥{total_fifo_rmb:,.2f}")
        print(f"   已分配: ¥{total_allocated_rmb:,.2f}")
        print(f"   理論總計: ¥{expected_balance:,.2f}")
        
        if abs(actual_balance - expected_balance) < 0.01:
            print("   ✅ 帳戶餘額與庫存一致！")
        else:
            print(f"   ❌ 不一致！差異: ¥{actual_balance - expected_balance:,.2f}")
            
            # 進一步分析
            print("\n🔍 6. 差異分析:")
            
            # 檢查是否有未關聯的庫存
            orphaned_inventory = db.session.execute(
                db.select(FIFOInventory)
                .filter(FIFOInventory.purchase_record_id.is_(None))
            ).scalars().all()
            
            if orphaned_inventory:
                print(f"   發現 {len(orphaned_inventory)} 個孤立的庫存記錄")
                for inv in orphaned_inventory:
                    print(f"     庫存 {inv.id}: ¥{inv.rmb_amount:,.2f}")
            
            # 檢查是否有未關聯的銷售記錄
            orphaned_sales = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.rmb_account_id.is_(None))
            ).scalars().all()
            
            if orphaned_sales:
                print(f"   發現 {len(orphaned_sales)} 個孤立的銷售記錄")
                for sale in orphaned_sales:
                    print(f"     銷售 {sale.id}: ¥{sale.rmb_amount:,.2f}")

if __name__ == "__main__":
    check_account_inventory_consistency()

