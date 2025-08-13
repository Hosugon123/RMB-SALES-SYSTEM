#!/usr/bin/env python3
"""
檢查現金管理相關的數據庫記錄
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_cash_management_data():
    """檢查現金管理數據"""
    
    print("=== 檢查現金管理數據 ===")
    
    try:
        # 嘗試導入app模組
        from app import app, db, Holder, CashAccount, PurchaseRecord, LedgerEntry, CashLog
        
        print("✓ 成功導入app模組")
        
        with app.app_context():
            print("\n1. 檢查帳戶餘額...")
            
            # 檢查所有帳戶
            accounts = db.session.execute(db.select(CashAccount)).scalars().all()
            for acc in accounts:
                print(f"   {acc.name} ({acc.currency}): {acc.balance:,.2f}")
            
            print("\n2. 檢查買入記錄...")
            
            # 檢查買入記錄
            purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
            for p in purchases:
                print(f"   買入記錄: RMB {p.rmb_amount:,.2f}, TWD成本 {p.twd_cost:,.2f}, 日期 {p.purchase_date}")
            
            print("\n3. 檢查記帳記錄...")
            
            # 檢查記帳記錄
            ledger_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
            for entry in ledger_entries:
                print(f"   記帳記錄: {entry.entry_type}, 金額 {entry.amount:,.2f}, 描述 {entry.description}")
            
            print("\n4. 檢查現金日誌...")
            
            # 檢查現金日誌
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
            for log in cash_logs:
                print(f"   現金日誌: {log.type}, 金額 {log.amount:,.2f}, 描述 {log.description}")
            
            print("\n5. 檢查持有人...")
            
            # 檢查持有人
            holders = db.session.execute(db.select(Holder).filter_by(is_active=True)).scalars().all()
            for holder in holders:
                print(f"   持有人: {holder.name}")
                for acc in holder.cash_accounts:
                    print(f"     - {acc.name} ({acc.currency}): {acc.balance:,.2f}")
            
    except ImportError as e:
        print(f"✗ 導入app模組失敗: {e}")
        return
    except Exception as e:
        print(f"✗ 檢查數據失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_cash_management_data()
