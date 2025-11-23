#!/usr/bin/env python3
"""
深度分析FIFO庫存與帳戶餘額同步問題的根本原因
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord, FIFOInventory, 
    FIFOSalesAllocation, LedgerEntry
)

def deep_analyze():
    """深度分析同步問題"""
    with app.app_context():
        print("=" * 80)
        print("深度分析：FIFO庫存與帳戶餘額同步問題")
        print("=" * 80)
        
        print("\n【關鍵問題1】售出時的扣款邏輯分析")
        print("-" * 80)
        
        # 檢查所有售出記錄
        all_sales = SalesRecord.query.all()
        print(f"總售出記錄數: {len(all_sales)}")
        
        mismatch_cases = []
        for sale in all_sales:
            if not sale.rmb_account_id:
                continue
                
            # 獲取該售出記錄的FIFO分配
            allocations = FIFOSalesAllocation.query.filter_by(sales_record_id=sale.id).all()
            
            # 檢查分配的庫存來源帳戶
            inventory_accounts = set()
            for alloc in allocations:
                inventory = FIFOInventory.query.get(alloc.fifo_inventory_id)
                if inventory and inventory.purchase_record:
                    deposit_account_id = inventory.purchase_record.deposit_account_id
                    if deposit_account_id:
                        inventory_accounts.add(deposit_account_id)
            
            # 扣款帳戶
            deduction_account_id = sale.rmb_account_id
            
            # 如果庫存來源帳戶和扣款帳戶不一致，就是問題！
            if inventory_accounts and deduction_account_id not in inventory_accounts:
                mismatch_cases.append({
                    'sale_id': sale.id,
                    'sale_rmb': sale.rmb_amount,
                    'deduction_account_id': deduction_account_id,
                    'inventory_account_ids': list(inventory_accounts),
                    'customer': sale.customer.name if sale.customer else 'N/A'
                })
        
        print(f"\n發現 {len(mismatch_cases)} 筆售出記錄存在扣款帳戶與庫存來源帳戶不一致的問題！")
        
        if mismatch_cases:
            print("\n問題案例詳情：")
            total_mismatch_rmb = 0
            for case in mismatch_cases[:10]:  # 只顯示前10個
                deduction_account = CashAccount.query.get(case['deduction_account_id'])
                deduction_name = deduction_account.name if deduction_account else f"ID:{case['deduction_account_id']}"
                
                inventory_names = []
                for acc_id in case['inventory_account_ids']:
                    acc = CashAccount.query.get(acc_id)
                    if acc:
                        inventory_names.append(acc.name)
                
                print(f"\n  售出記錄 ID {case['sale_id']} (客戶: {case['customer']}):")
                print(f"    售出金額: {case['sale_rmb']:,.2f} RMB")
                print(f"    扣款帳戶: {deduction_name} (ID: {case['deduction_account_id']})")
                print(f"    庫存來源帳戶: {', '.join(inventory_names)} (IDs: {case['inventory_account_ids']})")
                print(f"    [問題] 從錯誤的帳戶扣款！")
                total_mismatch_rmb += case['sale_rmb']
            
            if len(mismatch_cases) > 10:
                print(f"\n  ... 還有 {len(mismatch_cases) - 10} 筆類似問題")
            
            print(f"\n  總計錯誤扣款金額: {total_mismatch_rmb:,.2f} RMB")
        
        print("\n【關鍵問題2】帳戶餘額計算邏輯分析")
        print("-" * 80)
        
        # 檢查每個RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                # 作為deposit_account的買入總額
                as_deposit_purchase = (
                    db.session.execute(
                        db.select(func.sum(PurchaseRecord.rmb_amount))
                        .select_from(PurchaseRecord)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 作為rmb_account的售出總額（從這個帳戶扣款的售出）
                as_deduction_sales = (
                    db.session.execute(
                        db.select(func.sum(SalesRecord.rmb_amount))
                        .select_from(SalesRecord)
                        .filter(SalesRecord.rmb_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 該帳戶的FIFO庫存（基於deposit_account）
                account_fifo = (
                    db.session.execute(
                        db.select(func.sum(FIFOInventory.remaining_rmb))
                        .select_from(FIFOInventory)
                        .join(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 計算從該帳戶庫存中實際被售出的金額
                # 這需要通過FIFOSalesAllocation來追蹤
                actual_sold_from_this_account = (
                    db.session.execute(
                        db.select(func.sum(FIFOSalesAllocation.allocated_rmb))
                        .select_from(FIFOSalesAllocation)
                        .join(FIFOInventory, FIFOSalesAllocation.fifo_inventory_id == FIFOInventory.id)
                        .join(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # LedgerEntry變動
                ledger_debits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == acc.id,
                        LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                ledger_credits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == acc.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                # 理論上的帳戶餘額
                theoretical_balance = as_deposit_purchase - actual_sold_from_this_account - ledger_debits + ledger_credits
                
                # 差異分析
                balance_vs_fifo = acc.balance - account_fifo
                balance_vs_theoretical = acc.balance - theoretical_balance
                deduction_vs_actual = as_deduction_sales - actual_sold_from_this_account
                
                if abs(balance_vs_fifo) > 0.01 or abs(deduction_vs_actual) > 0.01:
                    print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                    print(f"  當前帳戶餘額: {acc.balance:,.2f} RMB")
                    print(f"  作為deposit_account的買入: {as_deposit_purchase:,.2f} RMB")
                    print(f"  作為deduction_account的售出扣款: {as_deduction_sales:,.2f} RMB")
                    print(f"  從該帳戶庫存實際售出: {actual_sold_from_this_account:,.2f} RMB")
                    print(f"  該帳戶的FIFO庫存: {account_fifo:,.2f} RMB")
                    print(f"  LedgerEntry扣款: {ledger_debits:,.2f} RMB")
                    print(f"  LedgerEntry入款: {ledger_credits:,.2f} RMB")
                    print(f"  理論帳戶餘額: {theoretical_balance:,.2f} RMB")
                    print(f"  扣款差異 (扣款帳戶售出 - 實際庫存售出): {deduction_vs_actual:,.2f} RMB")
                    print(f"  餘額 vs FIFO差異: {balance_vs_fifo:,.2f} RMB")
                    print(f"  餘額 vs 理論差異: {balance_vs_theoretical:,.2f} RMB")
                    
                    if abs(deduction_vs_actual) > 0.01:
                        print(f"  [嚴重問題] 從該帳戶扣款 {as_deduction_sales:,.2f}，但只從該帳戶庫存售出 {actual_sold_from_this_account:,.2f}")
                        print(f"  這意味著有 {deduction_vs_actual:,.2f} RMB 被錯誤扣款！")
        
        print("\n" + "=" * 80)
        print("【根本原因總結】")
        print("=" * 80)
        print("""
問題核心：

1. **售出時的扣款邏輯錯誤**：
   - 當前邏輯：從 sales_record.rmb_account_id（售出扣款戶）扣款
   - FIFO庫存分配：從所有可用庫存中按FIFO順序分配（可能來自不同帳戶）
   - 結果：扣款帳戶和庫存來源帳戶不一致！

2. **帳戶餘額計算錯誤**：
   - 帳戶餘額應該 = 該帳戶作為deposit_account的買入 - 從該帳戶庫存實際售出
   - 但當前系統：帳戶餘額 = 該帳戶作為deposit_account的買入 - 從該帳戶扣款的售出
   - 這兩個值可能完全不同！

3. **數據不一致的累積效應**：
   - 每次售出時，如果扣款帳戶 ≠ 庫存來源帳戶，就會產生差異
   - 差異會累積，導致數據完全錯誤

正確的邏輯應該是：
- 售出時，應該從庫存來源帳戶扣款（不是從指定的扣款帳戶）
- 或者：售出時不扣款，只扣FIFO庫存，帳戶餘額 = FIFO庫存總和
        """)

if __name__ == "__main__":
    deep_analyze()

