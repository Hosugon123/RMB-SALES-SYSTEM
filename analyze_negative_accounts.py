#!/usr/bin/env python3
"""
分析負值帳戶的原因
檢查是否有歷史數據問題或業務邏輯問題
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

def analyze_negative_accounts():
    """分析負值帳戶"""
    with app.app_context():
        print("=" * 80)
        print("分析負值帳戶的原因")
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
        
        if not negative_accounts:
            print("沒有發現負值帳戶")
            return
        
        print(f"\n發現 {len(negative_accounts)} 個負值帳戶：")
        print("-" * 80)
        
        for acc_info in negative_accounts:
            print(f"\n【負值帳戶】{acc_info['holder']}-{acc_info['account']} (ID: {acc_info['account_id']})")
            print(f"  買入總額: {acc_info['deposit_amount']:,.2f} RMB")
            print(f"  售出扣款總額: {acc_info['sales_amount']:,.2f} RMB")
            print(f"  當前餘額: {acc_info['balance']:,.2f} RMB")
            print(f"  超扣金額: {abs(acc_info['balance']):,.2f} RMB")
            
            # 檢查該帳戶的所有售出記錄
            sales_records = SalesRecord.query.filter_by(rmb_account_id=acc_info['account_id']).order_by(SalesRecord.created_at).all()
            
            print(f"\n  該帳戶的售出記錄詳情 ({len(sales_records)} 筆):")
            
            # 按時間順序分析，模擬餘額變化
            running_balance = acc_info['deposit_amount']
            problematic_sales = []
            
            for sale in sales_records:
                sale_rmb = sale.rmb_amount
                balance_before = running_balance
                running_balance -= sale_rmb
                balance_after = running_balance
                
                # 檢查庫存來源
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
                
                # 如果扣款後餘額變負，記錄為問題記錄
                if balance_after < 0 and balance_before >= 0:
                    problematic_sales.append({
                        'sale_id': sale.id,
                        'sale_rmb': sale_rmb,
                        'balance_before': balance_before,
                        'balance_after': balance_after,
                        'inventory_sources': inventory_sources,
                        'created_at': sale.created_at
                    })
                
                if len(sales_records) <= 20 or sale in sales_records[:10] or sale in sales_records[-10:]:
                    print(f"    售出 ID {sale.id} ({sale.created_at.strftime('%Y-%m-%d %H:%M:%S') if sale.created_at else 'N/A'}):")
                    print(f"      金額: {sale_rmb:,.2f} RMB")
                    print(f"      扣款前餘額: {balance_before:,.2f} RMB")
                    print(f"      扣款後餘額: {balance_after:,.2f} RMB")
                    if inventory_sources:
                        print(f"      庫存來源: {', '.join([f'{k}({v:,.2f})' for k, v in inventory_sources.items()])}")
                    if balance_after < 0:
                        print(f"      [問題] 扣款後餘額變負！")
            
            if problematic_sales:
                print(f"\n  [發現問題] 有 {len(problematic_sales)} 筆售出記錄導致餘額變負：")
                for ps in problematic_sales:
                    print(f"    售出 ID {ps['sale_id']} ({ps['created_at'].strftime('%Y-%m-%d %H:%M:%S') if ps['created_at'] else 'N/A'}):")
                    print(f"      扣款 {ps['sale_rmb']:,.2f} RMB，餘額從 {ps['balance_before']:,.2f} 變為 {ps['balance_after']:,.2f}")
                    if ps['inventory_sources']:
                        print(f"      庫存來源: {', '.join([f'{k}({v:,.2f})' for k, v in ps['inventory_sources'].items()])}")
        
        print("\n" + "=" * 80)
        print("【問題分析】")
        print("=" * 80)
        print("""
負值帳戶的原因：

1. **售出扣款 > 買入總額**
   - 這些帳戶的售出扣款總額超過了買入總額
   - 這表示從這些帳戶扣款的售出，但庫存是從其他帳戶買入的

2. **可能的業務邏輯問題**
   - 根據業務邏輯，售出時應該檢查帳戶餘額是否足夠
   - 如果餘額不足，不應該允許售出
   - 但歷史數據中可能存在餘額不足的售出記錄

3. **解決方案**
   - 選項A：修復歷史數據 - 將這些售出的扣款帳戶改為庫存來源帳戶
   - 選項B：允許負值 - 如果業務邏輯允許帳戶餘額為負（表示借用其他帳戶的庫存）
   - 選項C：調整計算邏輯 - 帳戶餘額 = 買入 - 從該帳戶庫存實際售出（而不是從該帳戶扣款的售出）
        """)
        print("=" * 80)

if __name__ == "__main__":
    analyze_negative_accounts()

