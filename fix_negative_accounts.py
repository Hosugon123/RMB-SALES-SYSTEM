#!/usr/bin/env python3
"""
修復負值帳戶 - 將售出記錄的扣款帳戶改為庫存來源帳戶
根據業務邏輯，帳戶餘額不應該為負值
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord, FIFOInventory, FIFOSalesAllocation
)

def fix_negative_accounts():
    """修復負值帳戶"""
    with app.app_context():
        print("=" * 80)
        print("修復負值帳戶")
        print("=" * 80)
        
        print("\n根據業務邏輯：")
        print("  帳戶餘額不應該為負值")
        print("  如果帳戶餘額為負，表示從該帳戶扣款的售出，但庫存來自其他帳戶")
        print("  解決方案：將這些售出的扣款帳戶改為庫存來源帳戶")
        
        # 獲取所有RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        negative_accounts = []
        
        # 先找出所有負值帳戶
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                deposit_amount = PurchaseRecord.query.filter(
                    PurchaseRecord.deposit_account_id == acc.id
                ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                
                sales_amount = SalesRecord.query.filter(
                    SalesRecord.rmb_account_id == acc.id
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                balance = deposit_amount - sales_amount
                
                if balance < 0:
                    negative_accounts.append({
                        'holder': holder.name,
                        'account': acc.name,
                        'account_id': acc.id,
                        'balance': balance,
                        'deposit_amount': deposit_amount,
                        'sales_amount': sales_amount
                    })
        
        if not negative_accounts:
            print("\n沒有發現負值帳戶")
            return
        
        print(f"\n發現 {len(negative_accounts)} 個負值帳戶")
        print("-" * 80)
        
        total_fixed = 0
        
        for acc_info in negative_accounts:
            print(f"\n【處理負值帳戶】{acc_info['holder']}-{acc_info['account']} (ID: {acc_info['account_id']})")
            print(f"  買入: {acc_info['deposit_amount']:,.2f} RMB")
            print(f"  售出扣款: {acc_info['sales_amount']:,.2f} RMB")
            print(f"  當前餘額: {acc_info['balance']:,.2f} RMB")
            
            # 獲取該帳戶的所有售出記錄
            sales_records = SalesRecord.query.filter_by(rmb_account_id=acc_info['account_id']).all()
            
            print(f"  該帳戶的售出記錄: {len(sales_records)} 筆")
            
            # 檢查每個售出記錄的庫存來源
            for sale in sales_records:
                allocations = FIFOSalesAllocation.query.filter_by(sales_record_id=sale.id).all()
                
                # 找出庫存來源帳戶
                inventory_source_accounts = {}
                for alloc in allocations:
                    inv = FIFOInventory.query.get(alloc.fifo_inventory_id)
                    if inv and inv.purchase_record and inv.purchase_record.deposit_account_id:
                        source_account_id = inv.purchase_record.deposit_account_id
                        if source_account_id not in inventory_source_accounts:
                            inventory_source_accounts[source_account_id] = 0
                        inventory_source_accounts[source_account_id] += alloc.allocated_rmb
                
                # 如果庫存來源帳戶與扣款帳戶不同，且扣款帳戶餘額會變負，則修改扣款帳戶
                if inventory_source_accounts:
                    # 使用庫存來源最多的帳戶作為扣款帳戶
                    main_source_account_id = max(inventory_source_accounts.items(), key=lambda x: x[1])[0]
                    
                    if main_source_account_id != sale.rmb_account_id:
                        source_account = CashAccount.query.get(main_source_account_id)
                        old_account = CashAccount.query.get(sale.rmb_account_id)
                        
                        print(f"    售出 ID {sale.id}: 從 {old_account.name if old_account else 'N/A'} 改為 {source_account.name if source_account else 'N/A'}")
                        sale.rmb_account_id = main_source_account_id
                        total_fixed += 1
        
        if total_fixed > 0:
            print(f"\n共修改了 {total_fixed} 筆售出記錄的扣款帳戶")
            print("提交更改...")
            db.session.commit()
            print("[成功] 修復完成！")
            
            # 重新計算帳戶餘額
            print("\n重新計算帳戶餘額...")
            for holder in holders:
                rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
                for acc in rmb_accounts:
                    deposit_amount = PurchaseRecord.query.filter(
                        PurchaseRecord.deposit_account_id == acc.id
                    ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                    
                    sales_amount = SalesRecord.query.filter(
                        SalesRecord.rmb_account_id == acc.id
                    ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                    
                    acc.balance = deposit_amount - sales_amount
            
            db.session.commit()
            print("[成功] 帳戶餘額已重新計算")
            
            # 驗證結果
            print("\n驗證結果：")
            remaining_negative = []
            for holder in holders:
                rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
                for acc in rmb_accounts:
                    if acc.balance < 0:
                        remaining_negative.append(f"{holder.name}-{acc.name} (餘額: {acc.balance:,.2f})")
            
            if remaining_negative:
                print(f"  仍有 {len(remaining_negative)} 個負值帳戶：")
                for acc_name in remaining_negative:
                    print(f"    - {acc_name}")
            else:
                print("  [成功] 所有帳戶餘額都為非負值！")
        else:
            print("\n沒有需要修復的記錄")
        
        print("=" * 80)

if __name__ == "__main__":
    fix_negative_accounts()

