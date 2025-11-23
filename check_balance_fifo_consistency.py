#!/usr/bin/env python3
"""
檢查帳戶餘額總和與FIFO庫存總和的一致性
根據業務邏輯，兩者應該一致
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

def check_consistency():
    """檢查帳戶餘額總和與FIFO庫存總和的一致性"""
    with app.app_context():
        print("=" * 80)
        print("檢查帳戶餘額總和與FIFO庫存總和的一致性")
        print("=" * 80)
        
        # 1. 計算全局FIFO庫存
        total_fifo = (
            db.session.execute(
                db.select(func.sum(FIFOInventory.remaining_rmb))
                .select_from(FIFOInventory)
            )
            .scalar()
        ) or 0.0
        
        # 2. 計算所有RMB帳戶餘額總和
        total_rmb_balance = (
            db.session.execute(
                db.select(func.sum(CashAccount.balance))
                .select_from(CashAccount)
                .filter(CashAccount.currency == "RMB")
                .filter(CashAccount.is_active == True)
            )
            .scalar()
        ) or 0.0
        
        print(f"\n【全局統計】")
        print(f"  全局FIFO庫存總和: {total_fifo:,.2f} RMB")
        print(f"  所有RMB帳戶餘額總和: {total_rmb_balance:,.2f} RMB")
        print(f"  差異: {total_rmb_balance - total_fifo:,.2f} RMB")
        
        # 3. 計算理論值
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
        
        print(f"\n【理論值】")
        print(f"  總買入: {total_purchase:,.2f} RMB")
        print(f"  總售出: {total_sales:,.2f} RMB")
        print(f"  理論FIFO庫存 (買入-售出): {theoretical_fifo:,.2f} RMB")
        
        # 4. 檢查各個帳戶
        print(f"\n【各帳戶詳情】")
        print("-" * 80)
        
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        account_summary = []
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                # 作為deposit_account的買入
                deposit_purchase = (
                    db.session.execute(
                        db.select(func.sum(PurchaseRecord.rmb_amount))
                        .select_from(PurchaseRecord)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 作為rmb_account的售出扣款
                deduction_sales = (
                    db.session.execute(
                        db.select(func.sum(SalesRecord.rmb_amount))
                        .select_from(SalesRecord)
                        .filter(SalesRecord.rmb_account_id == acc.id)
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
                
                # 理論帳戶餘額
                theoretical_balance = deposit_purchase - deduction_sales - ledger_debits + ledger_credits
                
                account_summary.append({
                    'holder': holder.name,
                    'account': acc.name,
                    'account_id': acc.id,
                    'current_balance': acc.balance,
                    'theoretical_balance': theoretical_balance,
                    'deposit_purchase': deposit_purchase,
                    'deduction_sales': deduction_sales,
                    'ledger_debits': ledger_debits,
                    'ledger_credits': ledger_credits,
                    'difference': acc.balance - theoretical_balance
                })
                
                print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                print(f"  當前餘額: {acc.balance:,.2f} RMB")
                print(f"  理論餘額: {theoretical_balance:,.2f} RMB")
                print(f"  買入: {deposit_purchase:,.2f} RMB")
                print(f"  售出扣款: {deduction_sales:,.2f} RMB")
                print(f"  LedgerEntry扣款: {ledger_debits:,.2f} RMB")
                print(f"  LedgerEntry入款: {ledger_credits:,.2f} RMB")
                print(f"  差異: {acc.balance - theoretical_balance:,.2f} RMB")
        
        # 5. 分析差異原因
        print(f"\n【差異分析】")
        print("-" * 80)
        
        # 計算所有帳戶的理論餘額總和
        total_theoretical_balance = sum(acc['theoretical_balance'] for acc in account_summary)
        
        print(f"  所有帳戶理論餘額總和: {total_theoretical_balance:,.2f} RMB")
        print(f"  所有帳戶實際餘額總和: {total_rmb_balance:,.2f} RMB")
        print(f"  全局FIFO庫存: {total_fifo:,.2f} RMB")
        
        # 檢查是否有LedgerEntry造成的差異
        total_ledger_credits = sum(acc['ledger_credits'] for acc in account_summary)
        total_ledger_debits = sum(acc['ledger_debits'] for acc in account_summary)
        net_ledger = total_ledger_credits - total_ledger_debits
        
        print(f"\n  LedgerEntry總入款: {total_ledger_credits:,.2f} RMB")
        print(f"  LedgerEntry總扣款: {total_ledger_debits:,.2f} RMB")
        print(f"  LedgerEntry淨變動: {net_ledger:,.2f} RMB")
        
        # 理論上：帳戶餘額總和 = FIFO庫存 + LedgerEntry淨變動
        expected_balance_sum = total_fifo + net_ledger
        print(f"\n  預期帳戶餘額總和 (FIFO庫存 {total_fifo:,.2f} + LedgerEntry淨變動 {net_ledger:,.2f}): {expected_balance_sum:,.2f} RMB")
        print(f"  實際帳戶餘額總和: {total_rmb_balance:,.2f} RMB")
        print(f"  差異: {total_rmb_balance - expected_balance_sum:,.2f} RMB")
        
        # 6. 檢查是否有其他問題
        print(f"\n【問題診斷】")
        print("-" * 80)
        
        if abs(total_rmb_balance - expected_balance_sum) > 0.01:
            print(f"  [問題] 帳戶餘額總和與預期值不一致！")
            print(f"  可能原因：")
            print(f"  1. 帳戶餘額計算錯誤")
            print(f"  2. 有未記錄的LedgerEntry變動")
            print(f"  3. 有手動修改的帳戶餘額")
            print(f"  4. 售出時的扣款邏輯有問題")
        else:
            print(f"  [正常] 帳戶餘額總和與預期值一致")
        
        # 檢查每個帳戶的差異
        print(f"\n【各帳戶差異詳情】")
        print("-" * 80)
        for acc in account_summary:
            if abs(acc['difference']) > 0.01:
                print(f"  {acc['holder']}-{acc['account']} (ID: {acc['account_id']}):")
                print(f"    當前餘額: {acc['current_balance']:,.2f} RMB")
                print(f"    理論餘額: {acc['theoretical_balance']:,.2f} RMB")
                print(f"    差異: {acc['difference']:,.2f} RMB")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    check_consistency()

