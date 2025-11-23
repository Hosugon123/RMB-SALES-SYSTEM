#!/usr/bin/env python3
"""
快速檢查FIFO庫存與帳戶餘額同步問題
可在Render Shell中執行
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord, FIFOInventory
)

with app.app_context():
    print("=" * 80)
    print("FIFO庫存與帳戶餘額同步檢查")
    print("=" * 80)
    
    # 1. 全局統計
    print("\n【1】全局統計")
    print("-" * 80)
    
    total_purchase_rmb = db.session.execute(
        db.select(func.sum(PurchaseRecord.rmb_amount))
    ).scalar() or 0.0
    
    total_sales_rmb = db.session.execute(
        db.select(func.sum(SalesRecord.rmb_amount))
    ).scalar() or 0.0
    
    total_global_fifo = db.session.execute(
        db.select(func.sum(FIFOInventory.remaining_rmb))
    ).scalar() or 0.0
    
    total_rmb_balance = db.session.execute(
        db.select(func.sum(CashAccount.balance))
        .select_from(CashAccount)
        .filter(CashAccount.currency == "RMB")
        .filter(CashAccount.is_active == True)
    ).scalar() or 0.0
    
    correct_global_fifo = total_purchase_rmb - total_sales_rmb
    
    print(f"所有買入RMB總和: {total_purchase_rmb:,.2f} RMB")
    print(f"所有售出RMB總和: {total_sales_rmb:,.2f} RMB")
    print(f"正確的全局FIFO庫存 (買入-售出): {correct_global_fifo:,.2f} RMB")
    print(f"實際的全局FIFO庫存: {total_global_fifo:,.2f} RMB")
    print(f"所有RMB帳戶餘額總和: {total_rmb_balance:,.2f} RMB")
    print(f"\n差異分析:")
    print(f"  FIFO庫存差異: {total_global_fifo - correct_global_fifo:,.2f} RMB")
    print(f"  帳戶餘額差異: {total_rmb_balance - correct_global_fifo:,.2f} RMB")
    print(f"  帳戶餘額 vs FIFO庫存: {total_rmb_balance - total_global_fifo:,.2f} RMB")
    
    # 2. 各帳戶檢查
    print("\n【2】各帳戶檢查")
    print("-" * 80)
    
    holders = db.session.execute(
        db.select(Holder).filter_by(is_active=True)
        .options(db.selectinload(Holder.cash_accounts))
    ).scalars().all()
    
    account_issues = []
    for holder in holders:
        rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
        for acc in rmb_accounts:
            # 該帳戶的FIFO庫存
            account_fifo = db.session.execute(
                db.select(func.sum(FIFOInventory.remaining_rmb))
                .select_from(FIFOInventory)
                .join(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                .filter(PurchaseRecord.deposit_account_id == acc.id)
            ).scalar() or 0.0
            
            # 該帳戶的買入
            account_purchase = db.session.execute(
                db.select(func.sum(PurchaseRecord.rmb_amount))
                .filter(PurchaseRecord.deposit_account_id == acc.id)
            ).scalar() or 0.0
            
            # 從該帳戶售出
            account_sales = db.session.execute(
                db.select(func.sum(SalesRecord.rmb_amount))
                .filter(SalesRecord.rmb_account_id == acc.id)
            ).scalar() or 0.0
            
            correct_fifo = account_purchase - account_sales
            difference = acc.balance - account_fifo
            
            print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
            print(f"  帳戶餘額: {acc.balance:,.2f} RMB")
            print(f"  實際FIFO庫存: {account_fifo:,.2f} RMB")
            print(f"  正確FIFO庫存 (買入{account_purchase:,.2f} - 售出{account_sales:,.2f}): {correct_fifo:,.2f} RMB")
            print(f"  差異: {difference:,.2f} RMB")
            
            if abs(difference) > 0.01:
                account_issues.append({
                    'account': f"{holder.name}-{acc.name}",
                    'balance': acc.balance,
                    'fifo': account_fifo,
                    'correct_fifo': correct_fifo,
                    'difference': difference
                })
                print(f"  ⚠️ 發現不一致！")
    
    # 3. 總結
    print("\n" + "=" * 80)
    print("總結")
    print("=" * 80)
    
    if abs(total_rmb_balance - correct_global_fifo) > 0.01:
        print(f"⚠️ 全局數據不一致！")
        print(f"  帳戶餘額總和與正確FIFO庫存差異: {total_rmb_balance - correct_global_fifo:,.2f} RMB")
    
    if abs(total_global_fifo - correct_global_fifo) > 0.01:
        print(f"⚠️ FIFO庫存數據不一致！")
        print(f"  實際FIFO庫存與正確FIFO庫存差異: {total_global_fifo - correct_global_fifo:,.2f} RMB")
    
    if len(account_issues) > 0:
        print(f"⚠️ 發現 {len(account_issues)} 個帳戶存在不一致:")
        for issue in account_issues:
            print(f"  - {issue['account']}: 差異 {issue['difference']:,.2f} RMB")
    else:
        print("✅ 所有帳戶數據一致")
    
    print("=" * 80)

