#!/usr/bin/env python3
"""
本地FIFO庫存與帳戶餘額同步修復腳本
用於診斷和修復本地數據庫中的同步問題
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func, and_
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord, FIFOInventory, 
    FIFOSalesAllocation, LedgerEntry
)

def diagnose_and_fix(auto_fix=False):
    """診斷並修復FIFO庫存與帳戶餘額同步問題
    
    Args:
        auto_fix: 如果為True，自動執行修復，無需確認
    """
    with app.app_context():
        print("=" * 80)
        print("FIFO庫存與帳戶餘額同步診斷與修復")
        print("=" * 80)
        
        # 1. 診斷階段
        print("\n【階段1】診斷當前狀態")
        print("-" * 80)
        
        # 獲取所有活躍的持有人和帳戶
        holders_with_accounts = (
            db.session.execute(
                db.select(Holder)
                .filter_by(is_active=True)
                .options(db.selectinload(Holder.cash_accounts))
            )
            .scalars()
            .all()
        )
        
        # 計算全局統計
        total_purchase_rmb = (
            db.session.execute(
                db.select(func.sum(PurchaseRecord.rmb_amount))
                .select_from(PurchaseRecord)
            )
            .scalar()
        ) or 0.0
        
        total_sales_rmb = (
            db.session.execute(
                db.select(func.sum(SalesRecord.rmb_amount))
                .select_from(SalesRecord)
            )
            .scalar()
        ) or 0.0
        
        total_global_fifo = (
            db.session.execute(
                db.select(func.sum(FIFOInventory.remaining_rmb))
                .select_from(FIFOInventory)
            )
            .scalar()
        ) or 0.0
        
        total_rmb_balance = (
            db.session.execute(
                db.select(func.sum(CashAccount.balance))
                .select_from(CashAccount)
                .filter(CashAccount.currency == "RMB")
                .filter(CashAccount.is_active == True)
            )
            .scalar()
        ) or 0.0
        
        correct_global_fifo = total_purchase_rmb - total_sales_rmb
        
        print(f"全局統計:")
        print(f"  所有買入RMB總和: {total_purchase_rmb:,.2f} RMB")
        print(f"  所有售出RMB總和: {total_sales_rmb:,.2f} RMB")
        print(f"  正確的全局FIFO庫存 (買入-售出): {correct_global_fifo:,.2f} RMB")
        print(f"  實際的全局FIFO庫存: {total_global_fifo:,.2f} RMB")
        print(f"  所有RMB帳戶餘額總和: {total_rmb_balance:,.2f} RMB")
        print(f"\n差異分析:")
        print(f"  FIFO庫存差異: {total_global_fifo - correct_global_fifo:,.2f} RMB")
        print(f"  帳戶餘額差異: {total_rmb_balance - correct_global_fifo:,.2f} RMB")
        print(f"  帳戶餘額 vs FIFO庫存: {total_rmb_balance - total_global_fifo:,.2f} RMB")
        
        # 檢查各個帳戶
        print("\n【階段2】檢查各個帳戶")
        print("-" * 80)
        
        account_issues = []
        for holder in holders_with_accounts:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                # 該帳戶的FIFO庫存總和
                account_fifo_inventory = (
                    db.session.execute(
                        db.select(func.sum(FIFOInventory.remaining_rmb))
                        .select_from(FIFOInventory)
                        .join(PurchaseRecord, FIFOInventory.purchase_record_id == PurchaseRecord.id)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 該帳戶的買入總和
                account_purchase_rmb = (
                    db.session.execute(
                        db.select(func.sum(PurchaseRecord.rmb_amount))
                        .select_from(PurchaseRecord)
                        .filter(PurchaseRecord.deposit_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # 從該帳戶售出的總和
                account_sales_rmb = (
                    db.session.execute(
                        db.select(func.sum(SalesRecord.rmb_amount))
                        .select_from(SalesRecord)
                        .filter(SalesRecord.rmb_account_id == acc.id)
                    )
                    .scalar()
                ) or 0.0
                
                # LedgerEntry中的額外變動
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
                
                # 正確的FIFO庫存 = 買入 - 售出（全局計算，不屬於特定帳戶）
                correct_fifo = account_purchase_rmb - account_sales_rmb
                
                # 正確的帳戶餘額 = 該帳戶作為deposit_account的買入 - 該帳戶作為rmb_account的售出扣款 + LedgerEntry變動
                # 注意：FIFO庫存是全局的，不屬於特定帳戶，所以不能基於FIFO庫存計算帳戶餘額
                correct_balance = account_purchase_rmb - account_sales_rmb - ledger_debits + ledger_credits
                
                # 差異 = 當前餘額 - 正確餘額
                account_difference = acc.balance - correct_balance
                
                print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                print(f"  當前帳戶餘額: {acc.balance:,.2f} RMB")
                print(f"  作為deposit_account的買入: {account_purchase_rmb:,.2f} RMB")
                print(f"  作為rmb_account的售出扣款: {account_sales_rmb:,.2f} RMB")
                print(f"  LedgerEntry扣款: {ledger_debits:,.2f} RMB")
                print(f"  LedgerEntry入款: {ledger_credits:,.2f} RMB")
                print(f"  正確帳戶餘額 (買入{account_purchase_rmb:,.2f} - 售出扣款{account_sales_rmb:,.2f} - Ledger扣款{ledger_debits:,.2f} + Ledger入款{ledger_credits:,.2f}): {correct_balance:,.2f} RMB")
                print(f"  差異: {account_difference:,.2f} RMB")
                print(f"  註：FIFO庫存是全局的，不屬於特定帳戶")
                
                if abs(account_difference) > 0.01:
                    account_issues.append({
                        'account_id': acc.id,
                        'account_name': f"{holder.name}-{acc.name}",
                        'holder_name': holder.name,
                        'current_balance': acc.balance,
                        'fifo_inventory': account_fifo_inventory,
                        'correct_balance': correct_balance,
                        'difference': account_difference
                    })
                    print(f"  [警告] 發現不一致！需要修復")
        
        # 3. 修復階段
        if len(account_issues) > 0:
            print("\n" + "=" * 80)
            print("【階段3】修復不一致的帳戶")
            print("=" * 80)
            
            if not auto_fix:
                try:
                    response = input(f"\n發現 {len(account_issues)} 個帳戶存在不一致，是否要修復？(y/n): ")
                    if response.lower() != 'y':
                        print("已取消修復")
                        return
                except EOFError:
                    print("\n[提示] 非交互模式，跳過修復。使用 --auto-fix 參數可自動修復")
                    return
            
            print("\n開始修復...")
            
            # 先修復FIFO庫存
            print("\n1. 修復FIFO庫存數據...")
            inventories = FIFOInventory.query.all()
            inventory_fixes = []
            for inventory in inventories:
                # 計算實際的已出帳數量（通過 FIFOSalesAllocation）
                actual_issued = db.session.query(func.sum(FIFOSalesAllocation.allocated_rmb)).filter(
                    FIFOSalesAllocation.fifo_inventory_id == inventory.id
                ).scalar() or 0
                
                old_remaining = inventory.remaining_rmb
                inventory.remaining_rmb = inventory.rmb_amount - actual_issued
                
                if abs(old_remaining - inventory.remaining_rmb) > 0.01:
                    inventory_fixes.append({
                        "batch_id": inventory.id,
                        "old_remaining": old_remaining,
                        "new_remaining": inventory.remaining_rmb
                    })
                    if abs(old_remaining - inventory.remaining_rmb) > 0.01:
                        print(f"  修復庫存批次 {inventory.id}: {old_remaining:,.2f} -> {inventory.remaining_rmb:,.2f} RMB")
            
            print(f"  共修復 {len(inventory_fixes)} 個庫存批次")
            
            # 修復帳戶餘額
            print("\n2. 修復RMB帳戶餘額...")
            account_fixes = []
            for issue in account_issues:
                account = CashAccount.query.get(issue['account_id'])
                if account and account.currency == "RMB":
                    old_balance = account.balance
                    
                    # 重新計算該帳戶的正確餘額
                    # 帳戶餘額 = 該帳戶作為deposit_account的買入 - 該帳戶作為rmb_account的售出扣款 + LedgerEntry變動
                    deposit_amount = PurchaseRecord.query.filter(
                        PurchaseRecord.deposit_account_id == account.id
                    ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                    
                    sales_amount = SalesRecord.query.filter(
                        SalesRecord.rmb_account_id == account.id
                    ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                    
                    # LedgerEntry中的額外變動
                    ledger_debits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT'])
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    ledger_credits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN'])
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    # 正確的帳戶餘額
                    new_balance = deposit_amount - sales_amount - ledger_debits + ledger_credits
                    
                    account.balance = new_balance
                    account_fixes.append({
                        "account_id": account.id,
                        "account_name": issue['account_name'],
                        "old_balance": old_balance,
                        "new_balance": new_balance
                    })
                    print(f"  修復帳戶 {issue['account_name']} (ID: {account.id}): {old_balance:,.2f} -> {new_balance:,.2f} RMB")
            
            print(f"  共修復 {len(account_fixes)} 個帳戶")
            
            # 提交更改
            print("\n3. 提交更改...")
            db.session.commit()
            print("  [成功] 修復完成！")
            
            # 驗證修復結果
            print("\n【階段4】驗證修復結果")
            print("-" * 80)
            
            total_rmb_balance_after = (
                db.session.execute(
                    db.select(func.sum(CashAccount.balance))
                    .select_from(CashAccount)
                    .filter(CashAccount.currency == "RMB")
                    .filter(CashAccount.is_active == True)
                )
                .scalar()
            ) or 0.0
            
            total_global_fifo_after = (
                db.session.execute(
                    db.select(func.sum(FIFOInventory.remaining_rmb))
                    .select_from(FIFOInventory)
                )
                .scalar()
            ) or 0.0
            
            print(f"修復後統計:")
            print(f"  所有RMB帳戶餘額總和: {total_rmb_balance_after:,.2f} RMB")
            print(f"  實際的全局FIFO庫存: {total_global_fifo_after:,.2f} RMB")
            print(f"  差異: {total_rmb_balance_after - total_global_fifo_after:,.2f} RMB")
            
            # 注意：帳戶餘額總和與FIFO庫存總和不一定相等
            # 因為：
            # 1. FIFO庫存是全局的，按FIFO原則減少
            # 2. 帳戶餘額是各帳戶獨立的，從指定帳戶扣款
            # 3. 如果售出時扣款帳戶 ≠ 庫存來源帳戶，就會有差異
            print("\n[提示] 帳戶餘額總和與FIFO庫存總和可能不一致，這是正常的")
            print("  因為FIFO庫存是全局的，而帳戶餘額是各帳戶獨立的")
        else:
            print("\n[成功] 所有帳戶數據一致，無需修復")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    import sys
    auto_fix = "--auto-fix" in sys.argv or "-y" in sys.argv
    diagnose_and_fix(auto_fix=auto_fix)

