#!/usr/bin/env python3
"""
檢查帳戶餘額的歷史變動
模擬從初始狀態開始，按時間順序計算餘額
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload
from app import (
    CashAccount, Holder, PurchaseRecord, SalesRecord, LedgerEntry
)

def check_balance_history():
    """檢查帳戶餘額的歷史變動"""
    with app.app_context():
        print("=" * 80)
        print("檢查帳戶餘額的歷史變動")
        print("=" * 80)
        
        # 獲取所有RMB帳戶
        holders = db.session.execute(
            db.select(Holder)
            .filter_by(is_active=True)
            .options(selectinload(Holder.cash_accounts))
        ).scalars().all()
        
        for holder in holders:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            for acc in rmb_accounts:
                print(f"\n{holder.name}-{acc.name} (ID: {acc.id}):")
                print("-" * 80)
                
                # 獲取所有買入記錄（按時間順序）
                purchases = PurchaseRecord.query.filter_by(
                    deposit_account_id=acc.id
                ).order_by(PurchaseRecord.purchase_date).all()
                
                # 獲取所有售出記錄（按時間順序）
                sales = SalesRecord.query.filter_by(
                    rmb_account_id=acc.id
                ).order_by(SalesRecord.created_at).all()
                
                # 獲取所有LedgerEntry記錄（按時間順序）
                ledger_entries = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == acc.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'WITHDRAW', 'TRANSFER_IN', 'TRANSFER_OUT'])
                    )
                ).order_by(LedgerEntry.entry_date).all()
                
                # 合併所有操作，按時間排序
                all_operations = []
                
                for p in purchases:
                    all_operations.append({
                        'type': 'PURCHASE',
                        'date': p.purchase_date,
                        'amount': p.rmb_amount,
                        'description': f"買入 {p.rmb_amount:,.2f} RMB"
                    })
                
                for s in sales:
                    all_operations.append({
                        'type': 'SALE',
                        'date': s.created_at,
                        'amount': -s.rmb_amount,
                        'description': f"售出扣款 {s.rmb_amount:,.2f} RMB"
                    })
                
                for le in ledger_entries:
                    all_operations.append({
                        'type': le.entry_type,
                        'date': le.entry_date,
                        'amount': le.amount,
                        'description': f"{le.entry_type} {le.amount:,.2f} RMB - {le.description or ''}"
                    })
                
                # 按時間排序
                all_operations.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
                
                # 模擬計算餘額
                simulated_balance = 0.0
                print(f"  模擬計算餘額（從0開始，按時間順序）：")
                
                for i, op in enumerate(all_operations[:20]):  # 只顯示前20筆
                    simulated_balance += op['amount']
                    date_str = op['date'].strftime('%Y-%m-%d %H:%M:%S') if op['date'] else 'N/A'
                    print(f"    {i+1}. {date_str}: {op['description']} -> 餘額: {simulated_balance:,.2f} RMB")
                
                if len(all_operations) > 20:
                    # 繼續計算剩餘的操作
                    for op in all_operations[20:]:
                        simulated_balance += op['amount']
                    
                    print(f"    ... 還有 {len(all_operations) - 20} 筆操作")
                    print(f"    最終模擬餘額: {simulated_balance:,.2f} RMB")
                else:
                    print(f"    最終模擬餘額: {simulated_balance:,.2f} RMB")
                
                # 當前餘額
                current_balance = acc.balance
                
                # 方法1：買入 - 售出扣款
                deposit_sum = sum(p.rmb_amount for p in purchases)
                sales_sum = sum(s.rmb_amount for s in sales)
                method1_balance = deposit_sum - sales_sum
                
                print(f"\n  對比：")
                print(f"    當前帳戶餘額（資料庫）: {current_balance:,.2f} RMB")
                print(f"    模擬計算餘額（含LedgerEntry）: {simulated_balance:,.2f} RMB")
                print(f"    方法1（買入 - 售出扣款）: {method1_balance:,.2f} RMB")
                print(f"    差異（當前 - 模擬）: {current_balance - simulated_balance:,.2f} RMB")
                print(f"    差異（當前 - 方法1）: {current_balance - method1_balance:,.2f} RMB")
                
                if abs(current_balance - method1_balance) > 0.01:
                    print(f"    [問題] 當前餘額與方法1不一致！")
                elif abs(current_balance - simulated_balance) > 0.01:
                    print(f"    [提示] 差異來自LedgerEntry變動")
                else:
                    print(f"    [正常] 餘額計算一致")
        
        print("\n" + "=" * 80)
        print("【總結】")
        print("=" * 80)
        print("""
根據分析：

1. **當前餘額 = 買入 - 售出扣款**（方法1）
   - 這表示帳戶餘額是通過累積操作得到的
   - 這是正確的計算方式

2. **如果帳面金額不符合實務金額，可能原因：**
   - 歷史數據有問題（某些買入或售出記錄不正確）
   - 有記錄被刪除但餘額未回滾
   - 有手動修改的餘額
   - 有其他未記錄的操作

3. **正確的修復方式：**
   - 不應該直接計算"買入 - 售出扣款"
   - 應該保持當前的餘額（因為它是通過實際操作累積的）
   - 或者：檢查是否有記錄被刪除，需要回滾餘額
        """)
        print("=" * 80)

if __name__ == "__main__":
    from datetime import datetime
    check_balance_history()

