#!/usr/bin/env python3
"""
詳細檢查負值帳戶的情況
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

def check_detail():
    """詳細檢查負值帳戶"""
    with app.app_context():
        print("=" * 80)
        print("詳細檢查負值帳戶")
        print("=" * 80)
        
        # 檢查特定帳戶
        account_ids = [23, 31]  # 7773-7773支付寶, 6186-6186支付寶
        
        for account_id in account_ids:
            acc = CashAccount.query.get(account_id)
            if not acc:
                continue
                
            print(f"\n【帳戶】{acc.holder.name if acc.holder else 'N/A'}-{acc.name} (ID: {account_id})")
            print("-" * 80)
            
            # 買入
            deposit_amount = PurchaseRecord.query.filter(
                PurchaseRecord.deposit_account_id == account_id
            ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
            
            # 售出扣款
            sales_amount = SalesRecord.query.filter(
                SalesRecord.rmb_account_id == account_id
            ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
            
            # 從該帳戶庫存實際售出
            actual_sold_from_this_account = (
                db.session.execute(
                    db.select(func.sum(FIFOSalesAllocation.allocated_rmb))
                    .select_from(FIFOSalesAllocation)
                    .join(FIFOInventory, FIFOSalesAllocation.fifo_inventory_id == FIFOInventory.id)
                    .join(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                    .filter(PurchaseRecord.deposit_account_id == account_id)
                )
                .scalar()
            ) or 0.0
            
            print(f"  買入總額: {deposit_amount:,.2f} RMB")
            print(f"  從該帳戶扣款的售出: {sales_amount:,.2f} RMB")
            print(f"  從該帳戶庫存實際售出: {actual_sold_from_this_account:,.2f} RMB")
            print(f"  當前餘額 (買入 - 扣款): {deposit_amount - sales_amount:,.2f} RMB")
            print(f"  理論餘額 (買入 - 實際售出): {deposit_amount - actual_sold_from_this_account:,.2f} RMB")
            
            # 檢查售出記錄
            sales_records = SalesRecord.query.filter_by(rmb_account_id=account_id).all()
            print(f"\n  該帳戶的售出記錄 ({len(sales_records)} 筆):")
            
            for sale in sales_records:
                allocations = FIFOSalesAllocation.query.filter_by(sales_record_id=sale.id).all()
                inventory_sources = {}
                for alloc in allocations:
                    inv = FIFOInventory.query.get(alloc.fifo_inventory_id)
                    if inv and inv.purchase_record:
                        source_account_id = inv.purchase_record.deposit_account_id
                        if source_account_id:
                            source_account = CashAccount.query.get(source_account_id)
                            source_name = f"{source_account.holder.name if source_account and source_account.holder else 'N/A'}-{source_account.name if source_account else f'ID:{source_account_id}'}"
                            if source_name not in inventory_sources:
                                inventory_sources[source_name] = 0
                            inventory_sources[source_name] += alloc.allocated_rmb
                
                print(f"    售出 ID {sale.id}: {sale.rmb_amount:,.2f} RMB")
                if inventory_sources:
                    print(f"      庫存來源: {', '.join([f'{k}({v:,.2f})' for k, v in inventory_sources.items()])}")
                    # 檢查是否從該帳戶扣款，但庫存來自其他帳戶
                    if account_id not in [inv.purchase_record.deposit_account_id for alloc in allocations for inv in [FIFOInventory.query.get(alloc.fifo_inventory_id)] if inv and inv.purchase_record]:
                        print(f"      [問題] 從該帳戶扣款，但庫存完全來自其他帳戶！")
        
        print("\n" + "=" * 80)
        print("【結論】")
        print("=" * 80)
        print("""
問題原因：
  這些帳戶的售出扣款 > 買入，導致負值
  這表示從這些帳戶扣款的售出，但庫存是從其他帳戶買入的

解決方案選項：
  1. 修改歷史售出記錄的扣款帳戶為庫存來源帳戶（會改變歷史數據）
  2. 調整計算邏輯：帳戶餘額 = 買入 - 從該帳戶庫存實際售出（而不是從該帳戶扣款的售出）
  3. 允許負值：如果業務邏輯允許帳戶餘額為負（表示借用其他帳戶的庫存）

根據您的業務邏輯，選項2最合理：
  - 帳戶餘額應該反映該帳戶實際擁有的庫存
  - 從該帳戶庫存實際售出的金額，才是真正從該帳戶減少的金額
        """)
        print("=" * 80)

if __name__ == "__main__":
    check_detail()

