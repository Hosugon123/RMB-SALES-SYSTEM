#!/usr/bin/env python3
"""
分析所有帳戶餘額計算邏輯
列出所有影響帳戶餘額的操作
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

def analyze_all_logic():
    """分析所有帳戶餘額計算邏輯"""
    with app.app_context():
        print("=" * 80)
        print("帳戶餘額計算邏輯完整分析")
        print("=" * 80)
        
        # 獲取所有RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        print("\n【算法1】實際運作時的帳戶餘額變動（從代碼中）")
        print("-" * 80)
        print("""
買入時（app.py 5252行）：
  deposit_account.balance += rmb_amount
  
售出時（app.py 994行）：
  deduction_account.balance -= rmb_amount
  
提款時（app.py 6202行）：
  account.balance -= amount
  
轉帳時：
  from_account.balance -= amount
  to_account.balance += amount
        """)
        
        print("\n【算法2】數據修復API中的計算（app.py 12072-12097行）")
        print("-" * 80)
        print("""
當前邏輯：
  帳戶餘額 = 買入 - 從該帳戶庫存實際售出
  
問題：
  - 忽略了實際運作時的累積過程
  - 忽略了其他可能的變動
        """)
        
        print("\n【算法3】修復腳本中的計算（fix_account_balance_exclude_ledger.py）")
        print("-" * 80)
        print("""
當前邏輯：
  帳戶餘額 = 買入 - 從該帳戶庫存實際售出
  
問題：
  - 與實際運作邏輯不一致
  - 直接計算，忽略了歷史累積
        """)
        
        print("\n【算法4】根據業務邏輯的正確計算")
        print("-" * 80)
        print("""
根據您提供的業務邏輯：
  帳戶餘額 = 該帳戶作為deposit_account的買入 - 該帳戶作為rmb_account的售出扣款
  
這意味著：
  - 買入時：餘額增加
  - 售出時：從指定帳戶扣款（不管庫存來源）
  - 帳戶餘額反映的是"該帳戶實際擁有的金額"
        """)
        
        print("\n【實際數據檢查】")
        print("-" * 80)
        
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                print(f"  當前帳戶餘額（資料庫中）: {acc.balance:,.2f} RMB")
                
                # 方法1：買入 - 售出扣款（根據業務邏輯）
                deposit_amount = PurchaseRecord.query.filter(
                    PurchaseRecord.deposit_account_id == acc.id
                ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                
                sales_deduction = SalesRecord.query.filter(
                    SalesRecord.rmb_account_id == acc.id
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                method1_balance = deposit_amount - sales_deduction
                print(f"  方法1（買入 - 售出扣款）: {method1_balance:,.2f} RMB")
                print(f"    買入: {deposit_amount:,.2f} RMB")
                print(f"    售出扣款: {sales_deduction:,.2f} RMB")
                
                # 方法2：買入 - 從該帳戶庫存實際售出
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
                
                method2_balance = deposit_amount - actual_sold_from_this_account
                print(f"  方法2（買入 - 庫存實際售出）: {method2_balance:,.2f} RMB")
                print(f"    買入: {deposit_amount:,.2f} RMB")
                print(f"    庫存實際售出: {actual_sold_from_this_account:,.2f} RMB")
                
                # 方法3：當前餘額 + LedgerEntry變動
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
                
                method3_balance = acc.balance - ledger_credits + ledger_debits
                print(f"  方法3（當前餘額 - LedgerEntry影響）: {method3_balance:,.2f} RMB")
                print(f"    當前餘額: {acc.balance:,.2f} RMB")
                print(f"    LedgerEntry入款: {ledger_credits:,.2f} RMB")
                print(f"    LedgerEntry扣款: {ledger_debits:,.2f} RMB")
                
                # 差異分析
                print(f"\n  差異分析：")
                print(f"    當前餘額 vs 方法1: {acc.balance - method1_balance:,.2f} RMB")
                print(f"    當前餘額 vs 方法2: {acc.balance - method2_balance:,.2f} RMB")
                print(f"    當前餘額 vs 方法3: {acc.balance - method3_balance:,.2f} RMB")
                print(f"    方法1 vs 方法2: {method1_balance - method2_balance:,.2f} RMB")
        
        print("\n" + "=" * 80)
        print("【問題診斷】")
        print("=" * 80)
        print("""
可能的問題：

1. **方法1 vs 方法2的差異**
   - 方法1：買入 - 售出扣款（從該帳戶扣款的售出）
   - 方法2：買入 - 庫存實際售出（從該帳戶庫存實際售出的）
   - 差異表示：從該帳戶扣款的售出，但庫存來自其他帳戶

2. **當前餘額 vs 方法1的差異**
   - 如果差異很大，表示帳戶餘額可能被其他操作影響
   - 或者歷史數據有問題

3. **正確的計算方式應該是：**
   - 根據業務邏輯，應該使用方法1：買入 - 售出扣款
   - 因為售出時是從指定帳戶扣款，不管庫存來源
        """)
        print("=" * 80)

if __name__ == "__main__":
    analyze_all_logic()

