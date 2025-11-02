#!/usr/bin/env python3
# 簡化版本：可以直接在 Render Shell 中創建並執行
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')
from app import app, db, LedgerEntry, CashAccount, SalesRecord, FIFOSalesAllocation, FIFOInventory

with app.app_context():
    # 查找目標帳戶
    accounts = {}
    for name in ['0107', '7773', '6186']:
        acc = db.session.execute(db.select(CashAccount).filter(CashAccount.currency=="RMB").filter(CashAccount.name.like(f"%{name}%支付寶%"))).scalar_one_or_none()
        if acc:
            accounts[name] = acc
    
    print("="*80)
    print("快速分析三個支付寶帳戶的 WITHDRAW 記錄")
    print("="*80)
    
    for name, account in accounts.items():
        print(f"\n{name} 支付寶 (ID: {account.id}):")
        print(f"  當前餘額: {account.balance:,.2f} RMB")
        
        # WITHDRAW 記錄
        withdraws = db.session.execute(
            db.select(LedgerEntry)
            .filter(LedgerEntry.entry_type=="WITHDRAW")
            .filter(LedgerEntry.description.like("%售出扣款%"))
            .filter(LedgerEntry.account_id==account.id)
        ).scalars().all()
        
        withdraw_total = sum(abs(r.amount) for r in withdraws)
        print(f"  WITHDRAW 總額: {withdraw_total:,.2f} RMB ({len(withdraws)} 筆)")
        
        # 銷售總額
        sales = db.session.execute(
            db.select(SalesRecord).filter(SalesRecord.rmb_account_id==account.id)
        ).scalars().all()
        sales_total = sum(s.rmb_amount for s in sales)
        print(f"  銷售總額: {sales_total:,.2f} RMB ({len(sales)} 筆)")
        
        # 使用此帳戶庫存的銷售（關鍵！）
        all_allocations = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
        inventory_total = 0
        for alloc in all_allocations:
            if alloc.fifo_inventory and alloc.fifo_inventory.purchase_record:
                source_account = alloc.fifo_inventory.purchase_record.deposit_account
                if source_account and source_account.id == account.id:
                    inventory_total += alloc.allocated_rmb
        
        print(f"  使用此帳戶庫存的總額: {inventory_total:,.2f} RMB")
        print(f"  理論餘額: {account.balance + withdraw_total:,.2f} RMB")
        
        # 差異分析
        diff_with_sales = withdraw_total - sales_total
        diff_with_inventory = withdraw_total - inventory_total
        print(f"  差異（與銷售總額）: {diff_with_sales:,.2f} RMB")
        print(f"  差異（與庫存總額）: {diff_with_inventory:,.2f} RMB")
        
        if abs(diff_with_inventory) < abs(diff_with_sales):
            print(f"  ✅ WITHDRAW 更接近庫存總額（證明 account_id 是庫存來源帳戶）")
        else:
            print(f"  ⚠️  WITHDRAW 更接近銷售總額")


