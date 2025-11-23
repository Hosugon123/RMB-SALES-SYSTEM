#!/usr/bin/env python3
"""
修復帳戶餘額計算 - 排除LedgerEntry影響
根據業務邏輯：帳戶餘額總和應該等於FIFO庫存總和
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord
)

def fix_account_balance():
    """修復帳戶餘額 - 排除LedgerEntry"""
    with app.app_context():
        print("=" * 80)
        print("修復帳戶餘額計算 - 排除LedgerEntry影響")
        print("=" * 80)
        
        print("\n根據業務邏輯：")
        print("  帳戶餘額 = 該帳戶作為deposit_account的買入 - 該帳戶作為rmb_account的售出扣款")
        print("  帳戶餘額總和應該等於FIFO庫存總和")
        print("  LedgerEntry是額外的記錄，不應該影響帳戶餘額")
        
        # 獲取所有RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        print("\n開始修復...")
        print("-" * 80)
        
        account_fixes = []
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                old_balance = acc.balance
                
                # 該帳戶作為deposit_account的買入總額
                deposit_amount = PurchaseRecord.query.filter(
                    PurchaseRecord.deposit_account_id == acc.id
                ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                
                # 該帳戶作為rmb_account的售出扣款總額
                sales_amount = SalesRecord.query.filter(
                    SalesRecord.rmb_account_id == acc.id
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                # 正確的帳戶餘額（排除LedgerEntry）
                new_balance = deposit_amount - sales_amount
                
                acc.balance = new_balance
                
                account_fixes.append({
                    'holder': holder.name,
                    'account': acc.name,
                    'account_id': acc.id,
                    'old_balance': old_balance,
                    'new_balance': new_balance,
                    'deposit_amount': deposit_amount,
                    'sales_amount': sales_amount
                })
                
                print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                print(f"  買入: {deposit_amount:,.2f} RMB")
                print(f"  售出扣款: {sales_amount:,.2f} RMB")
                print(f"  舊餘額: {old_balance:,.2f} RMB")
                print(f"  新餘額: {new_balance:,.2f} RMB")
                print(f"  變化: {new_balance - old_balance:,.2f} RMB")
        
        # 提交更改
        print("\n" + "-" * 80)
        print("提交更改...")
        db.session.commit()
        print("[成功] 修復完成！")
        
        # 驗證結果
        print("\n" + "=" * 80)
        print("驗證結果")
        print("=" * 80)
        
        total_rmb_balance = (
            db.session.execute(
                db.select(func.sum(CashAccount.balance))
                .select_from(CashAccount)
                .filter(CashAccount.currency == "RMB")
                .filter(CashAccount.is_active == True)
            )
            .scalar()
        ) or 0.0
        
        # 計算理論FIFO庫存
        total_purchase = (
            db.session.execute(
                db.select(func.sum(PurchaseRecord.rmb_amount))
                .select_from(PurchaseRecord)
            )
            .scalar()
        ) or 0.0
        
        total_sales = (
            db.session.execute(
                db.select(func.sum(SalesRecord.rmb_amount))
                .select_from(SalesRecord)
            )
            .scalar()
        ) or 0.0
        
        theoretical_fifo = total_purchase - total_sales
        
        print(f"  所有RMB帳戶餘額總和: {total_rmb_balance:,.2f} RMB")
        print(f"  理論FIFO庫存 (買入 {total_purchase:,.2f} - 售出 {total_sales:,.2f}): {theoretical_fifo:,.2f} RMB")
        print(f"  差異: {total_rmb_balance - theoretical_fifo:,.2f} RMB")
        
        if abs(total_rmb_balance - theoretical_fifo) < 0.01:
            print("\n[成功] 帳戶餘額總和 = FIFO庫存總和！")
        else:
            print("\n[警告] 仍有差異，需要進一步檢查")
        
        print("=" * 80)

if __name__ == "__main__":
    fix_account_balance()

