#!/usr/bin/env python3
"""
分析LedgerEntry記錄，找出造成差異的原因
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func, and_
from app import (
    CashAccount, LedgerEntry
)

def analyze_ledger():
    """分析LedgerEntry記錄"""
    with app.app_context():
        print("=" * 80)
        print("分析LedgerEntry記錄")
        print("=" * 80)
        
        # 獲取所有RMB帳戶
        rmb_accounts = CashAccount.query.filter_by(currency="RMB", is_active=True).all()
        
        total_credits = 0
        total_debits = 0
        
        for acc in rmb_accounts:
            print(f"\n帳戶: {acc.name} (ID: {acc.id})")
            print("-" * 80)
            
            # 入款記錄
            credits = LedgerEntry.query.filter(
                and_(
                    LedgerEntry.account_id == acc.id,
                    LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN'])
                )
            ).order_by(LedgerEntry.entry_date).all()
            
            # 扣款記錄
            debits = LedgerEntry.query.filter(
                and_(
                    LedgerEntry.account_id == acc.id,
                    LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT'])
                )
            ).order_by(LedgerEntry.entry_date).all()
            
            account_credits = sum(entry.amount for entry in credits)
            account_debits = abs(sum(entry.amount for entry in debits))
            
            print(f"  入款記錄數: {len(credits)}")
            if credits:
                for entry in credits:
                    date_str = entry.entry_date.strftime('%Y-%m-%d %H:%M:%S') if entry.entry_date else 'N/A'
                    print(f"    - {date_str}: {entry.entry_type} {entry.amount:,.2f} RMB - {entry.description or 'N/A'}")
            
            print(f"  扣款記錄數: {len(debits)}")
            if debits:
                for entry in debits:
                    date_str = entry.entry_date.strftime('%Y-%m-%d %H:%M:%S') if entry.entry_date else 'N/A'
                    print(f"    - {date_str}: {entry.entry_type} {entry.amount:,.2f} RMB - {entry.description or 'N/A'}")
            
            print(f"  總入款: {account_credits:,.2f} RMB")
            print(f"  總扣款: {account_debits:,.2f} RMB")
            print(f"  淨變動: {account_credits - account_debits:,.2f} RMB")
            
            total_credits += account_credits
            total_debits += account_debits
        
        print(f"\n" + "=" * 80)
        print(f"總計:")
        print(f"  所有帳戶總入款: {total_credits:,.2f} RMB")
        print(f"  所有帳戶總扣款: {total_debits:,.2f} RMB")
        print(f"  淨變動: {total_credits - total_debits:,.2f} RMB")
        print("=" * 80)

if __name__ == "__main__":
    analyze_ledger()

