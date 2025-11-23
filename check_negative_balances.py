#!/usr/bin/env python3
"""
檢查負值帳戶餘額的原因
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

def check_negative_balances():
    """檢查負值帳戶餘額的原因"""
    with app.app_context():
        print("=" * 80)
        print("檢查負值帳戶餘額的原因")
        print("=" * 80)
        
        # 獲取所有RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        negative_accounts = []
        
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                # 計算帳戶餘額
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
                    
                    print(f"\n[負值帳戶] {holder.name}-{acc.name} (ID: {acc.id}):")
                    print(f"  買入: {deposit_amount:,.2f} RMB")
                    print(f"  售出扣款: {sales_amount:,.2f} RMB")
                    print(f"  餘額: {balance:,.2f} RMB")
                    print(f"  差異: {sales_amount - deposit_amount:,.2f} RMB (售出扣款 > 買入)")
                    
                    # 檢查該帳戶的售出記錄
                    sales_records = SalesRecord.query.filter_by(rmb_account_id=acc.id).all()
                    print(f"\n  該帳戶的售出記錄 ({len(sales_records)} 筆):")
                    
                    for sale in sales_records[:10]:  # 只顯示前10筆
                        # 檢查這些售出的庫存來源
                        allocations = FIFOSalesAllocation.query.filter_by(sales_record_id=sale.id).all()
                        inventory_sources = {}
                        for alloc in allocations:
                            inv = FIFOInventory.query.get(alloc.fifo_inventory_id)
                            if inv and inv.purchase_record:
                                source_account_id = inv.purchase_record.deposit_account_id
                                if source_account_id:
                                    source_account = CashAccount.query.get(source_account_id)
                                    source_name = source_account.name if source_account else f"ID:{source_account_id}"
                                    if source_name not in inventory_sources:
                                        inventory_sources[source_name] = 0
                                    inventory_sources[source_name] += alloc.allocated_rmb
                        
                        print(f"    售出 ID {sale.id}: {sale.rmb_amount:,.2f} RMB")
                        if inventory_sources:
                            print(f"      庫存來源: {', '.join([f'{k}({v:,.2f})' for k, v in inventory_sources.items()])}")
                        else:
                            print(f"      庫存來源: 無")
                    
                    if len(sales_records) > 10:
                        print(f"    ... 還有 {len(sales_records) - 10} 筆售出記錄")
        
        print("\n" + "=" * 80)
        print("【分析】")
        print("=" * 80)
        
        if negative_accounts:
            print(f"發現 {len(negative_accounts)} 個負值帳戶")
            print("\n原因分析：")
            print("  這些帳戶的售出扣款總額 > 買入總額")
            print("  這表示：從這些帳戶扣款的售出，但庫存是從其他帳戶買入的")
            print("\n可能的解決方案：")
            print("  1. 檢查是否有歷史數據錯誤")
            print("  2. 檢查售出時的扣款邏輯是否正確")
            print("  3. 如果業務邏輯允許，負值可能是正常的（表示該帳戶借用了其他帳戶的庫存）")
        else:
            print("沒有發現負值帳戶")
        
        print("=" * 80)

if __name__ == "__main__":
    check_negative_balances()

