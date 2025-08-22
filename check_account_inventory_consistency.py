#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查帳戶數據和庫存數據的一致性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import CashAccount, FIFOInventory, PurchaseRecord, FIFOSalesAllocation

def check_consistency():
    """檢查帳戶餘額和庫存數據的一致性"""
    print("🔍 開始檢查帳戶數據和庫存數據的一致性...")
    
    with app.app_context():
        try:
            # 1. 獲取所有RMB帳戶的總餘額
            rmb_accounts = db.session.execute(
                db.select(CashAccount).filter_by(currency="RMB", is_active=True)
            ).scalars().all()
            
            total_account_rmb = sum(acc.balance for acc in rmb_accounts)
            print(f"📊 帳戶總RMB餘額: {total_account_rmb:,.2f}")
            
            # 2. 獲取FIFO庫存的總剩餘RMB
            all_inventory = db.session.execute(db.select(FIFOInventory)).scalars().all()
            total_inventory_rmb = sum(inv.remaining_rmb for inv in all_inventory)
            print(f"📦 FIFO庫存總剩餘RMB: {total_inventory_rmb:,.2f}")
            
            # 3. 計算差異
            difference = total_account_rmb - total_inventory_rmb
            print(f"⚠️  差異: {difference:,.2f}")
            
            if abs(difference) > 0.01:  # 允許0.01的浮點數誤差
                print("❌ 帳戶數據和庫存數據不一致！")
                
                # 4. 詳細分析每個帳戶
                print("\n📋 詳細帳戶分析:")
                for acc in rmb_accounts:
                    print(f"  - {acc.name}: {acc.balance:,.2f} RMB")
                
                # 5. 詳細分析庫存
                print("\n📦 詳細庫存分析:")
                for inv in all_inventory:
                    purchase = inv.purchase_record
                    if purchase and purchase.deposit_account:
                        print(f"  - 批次 {inv.id}: {inv.remaining_rmb:,.2f} RMB (帳戶: {purchase.deposit_account.name})")
                    else:
                        print(f"  - 批次 {inv.id}: {inv.remaining_rmb:,.2f} RMB (無關聯帳戶)")
                
                return False
            else:
                print("✅ 帳戶數據和庫存數據一致！")
                return True
                
        except Exception as e:
            print(f"❌ 檢查過程中發生錯誤: {e}")
            return False

def fix_consistency():
    """嘗試修復一致性问题"""
    print("\n🔧 開始嘗試修復一致性问题...")
    
    with app.app_context():
        try:
            # 1. 檢查是否有未關聯的庫存記錄
            orphaned_inventory = db.session.execute(
                db.select(FIFOInventory)
                .outerjoin(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                .filter(PurchaseRecord.id.is_(None))
            ).scalars().all()
            
            if orphaned_inventory:
                print(f"⚠️  發現 {len(orphaned_inventory)} 個孤立的庫存記錄")
                for inv in orphaned_inventory:
                    print(f"  - 庫存ID {inv.id}: {inv.remaining_rmb:,.2f} RMB")
            
            # 2. 檢查是否有庫存分配但帳戶餘額未扣減的情況
            allocations = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
            print(f"📊 總共有 {len(allocations)} 個庫存分配記錄")
            
            # 3. 建議的修復方案
            print("\n💡 建議的修復方案:")
            print("1. 檢查是否有銷售記錄創建但庫存未正確扣減")
            print("2. 檢查是否有帳戶餘額變更但未記錄在流水中的情況")
            print("3. 檢查是否有手動修改帳戶餘額但未同步庫存的情況")
            
            return True
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 帳戶數據和庫存數據一致性檢查工具")
    print("=" * 60)
    
    # 檢查一致性
    is_consistent = check_consistency()
    
    if not is_consistent:
        # 嘗試修復
        fix_consistency()
    
    print("\n" + "=" * 60)
    print("✅ 檢查完成")
    print("=" * 60)
