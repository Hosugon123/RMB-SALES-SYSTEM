#!/usr/bin/env python3
# 這是可以在 Render Shell 中一行一行輸入的版本
# 或者直接執行: python -c "$(cat VERIFY_SALES_ONE_LINER.py)"

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')
from app import app, db, SalesRecord, LedgerEntry, Customer, CashAccount

with app.app_context():
    # 1. 總售出
    all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    total_sales_rmb = sum(s.rmb_amount for s in all_sales)
    total_sales_twd = sum(s.twd_amount for s in all_sales)
    
    # 2. 總銷帳
    all_settlements = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == "SETTLEMENT")).scalars().all()
    total_settlements = sum(s.amount for s in all_settlements)
    
    # 3. 應收帳款
    all_customers = db.session.execute(db.select(Customer)).scalars().all()
    total_receivables = sum(c.total_receivables_twd for c in all_customers)
    calculated_receivables = total_sales_twd - total_settlements
    
    # 4. WITHDRAW 記錄
    withdraw_records = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == "WITHDRAW").filter(LedgerEntry.description.like("%售出扣款%"))).scalars().all()
    total_withdraw_rmb = sum(abs(r.amount) for r in withdraw_records)
    
    print("="*80)
    print("數據驗證報告")
    print("="*80)
    print(f"1. 歷史總售出: {total_sales_twd:,.2f} TWD ({total_sales_rmb:,.2f} RMB)")
    print(f"2. 歷史總銷帳: {total_settlements:,.2f} TWD")
    print(f"3. 應收帳款（計算）: {calculated_receivables:,.2f} TWD")
    print(f"4. 應收帳款（資料庫）: {total_receivables:,.2f} TWD")
    print(f"5. 售出扣款 WITHDRAW: {total_withdraw_rmb:,.2f} RMB ({len(withdraw_records)} 筆)")
    print(f"6. WITHDRAW/總售出比例: {total_withdraw_rmb/total_sales_rmb*100 if total_sales_rmb > 0 else 0:.2f}%")
    print("="*80)

