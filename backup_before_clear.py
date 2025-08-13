#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據備份腳本 - 清空前備份
在清空數據前備份重要信息
"""

import sys
import os
import json
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    # 從app.py導入模型類
    from app import (
        PurchaseRecord, SalesRecord, CardPurchase, LedgerEntry, CashLog,
        FIFOInventory, FIFOSalesAllocation, CashAccount, Customer,
        User, Holder, Channel, PaymentAccount, DepositAccount
    )
    
    print("✅ 模型導入成功")
    print("💾 數據備份腳本 - 清空前備份")
    print("=" * 50)
    
    with app.app_context():
        # 創建備份目錄
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/backup_{timestamp}.json"
        
        print(f"📁 備份文件: {backup_file}")
        
        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "summary": {},
            "data": {}
        }
        
        # 備份系統基礎結構
        print("1. 備份系統基礎結構...")
        
        # 用戶
        users = db.session.execute(db.select(User)).scalars().all()
        backup_data["data"]["users"] = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_active": u.is_active,
                "is_admin": u.is_admin
            } for u in users
        ]
        
        # 持有人
        holders = db.session.execute(db.select(Holder)).scalars().all()
        backup_data["data"]["holders"] = [
            {
                "id": h.id,
                "name": h.name,
                "is_active": h.is_active
            } for h in holders
        ]
        
        # 現金帳戶
        cash_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        backup_data["data"]["cash_accounts"] = [
            {
                "id": acc.id,
                "name": acc.name,
                "currency": acc.currency,
                "holder_id": acc.holder_id,
                "balance": acc.balance
            } for acc in cash_accounts
        ]
        
        # 客戶
        customers = db.session.execute(db.select(Customer)).scalars().all()
        backup_data["data"]["customers"] = [
            {
                "id": c.id,
                "name": c.name,
                "is_active": c.is_active,
                "total_receivables_twd": c.total_receivables_twd
            } for c in customers
        ]
        
        # 渠道
        channels = db.session.execute(db.select(Channel)).scalars().all()
        backup_data["data"]["channels"] = [
            {
                "id": ch.id,
                "name": ch.name,
                "is_active": ch.is_active
            } for ch in channels
        ]
        
        # 付款/收款帳戶
        payment_accounts = db.session.execute(db.select(PaymentAccount)).scalars().all()
        backup_data["data"]["payment_accounts"] = [
            {
                "id": acc.id,
                "name": acc.name,
                "is_active": acc.is_active
            } for acc in payment_accounts
        ]
        
        deposit_accounts = db.session.execute(db.select(DepositAccount)).scalars().all()
        backup_data["data"]["deposit_accounts"] = [
            {
                "id": acc.id,
                "name": acc.name,
                "is_active": acc.is_active
            } for acc in deposit_accounts
        ]
        
        # 備份交易數據摘要（不備份詳細內容）
        print("2. 備份交易數據摘要...")
        
        # 買入記錄摘要
        purchase_records = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        backup_data["data"]["purchase_summary"] = {
            "total_count": len(purchase_records),
            "total_rmb": sum(p.rmb_amount for p in purchase_records),
            "total_twd": sum(p.twd_cost for p in purchase_records),
            "date_range": {
                "earliest": min(p.purchase_date for p in purchase_records).isoformat() if purchase_records else None,
                "latest": max(p.purchase_date for p in purchase_records).isoformat() if purchase_records else None
            }
        }
        
        # 銷售記錄摘要
        sales_records = db.session.execute(db.select(SalesRecord)).scalars().all()
        backup_data["data"]["sales_summary"] = {
            "total_count": len(sales_records),
            "total_rmb": sum(s.rmb_amount for s in sales_records),
            "total_twd": sum(s.twd_amount for s in sales_records),
            "date_range": {
                "earliest": min(s.created_at for s in sales_records).isoformat() if sales_records else None,
                "latest": max(s.created_at for s in sales_records).isoformat() if sales_records else None
            }
        }
        
        # FIFO庫存摘要
        fifo_inventories = db.session.execute(db.select(FIFOInventory)).scalars().all()
        backup_data["data"]["fifo_summary"] = {
            "total_count": len(fifo_inventories),
            "total_remaining_rmb": sum(inv.remaining_rmb for inv in fifo_inventories),
            "total_original_rmb": sum(inv.original_rmb for inv in fifo_inventories)
        }
        
        # 記帳記錄摘要
        ledger_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
        backup_data["data"]["ledger_summary"] = {
            "total_count": len(ledger_entries),
            "total_amount": sum(entry.amount for entry in ledger_entries)
        }
        
        # 現金日誌摘要
        cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        backup_data["data"]["cash_log_summary"] = {
            "total_count": len(cash_logs),
            "total_amount": sum(log.amount for log in cash_logs)
        }
        
        # 計算總摘要
        backup_data["summary"] = {
            "total_users": len(users),
            "total_holders": len(holders),
            "total_cash_accounts": len(cash_accounts),
            "total_customers": len(customers),
            "total_channels": len(channels),
            "total_payment_accounts": len(payment_accounts),
            "total_deposit_accounts": len(deposit_accounts),
            "total_purchases": len(purchase_records),
            "total_sales": len(sales_records),
            "total_fifo_inventories": len(fifo_inventories),
            "total_ledger_entries": len(ledger_entries),
            "total_cash_logs": len(cash_logs),
            "total_account_balance": sum(acc.balance for acc in cash_accounts),
            "total_receivables": sum(c.total_receivables_twd for c in customers)
        }
        
        # 保存備份文件
        print("3. 保存備份文件...")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 備份完成！文件保存至: {backup_file}")
        print("\n📊 備份摘要:")
        print(f"   - 用戶: {backup_data['summary']['total_users']}")
        print(f"   - 持有人: {backup_data['summary']['total_holders']}")
        print(f"   - 現金帳戶: {backup_data['summary']['total_cash_accounts']}")
        print(f"   - 客戶: {backup_data['summary']['total_customers']}")
        print(f"   - 渠道: {backup_data['summary']['total_channels']}")
        print(f"   - 買入記錄: {backup_data['summary']['total_purchases']}")
        print(f"   - 銷售記錄: {backup_data['summary']['total_sales']}")
        print(f"   - FIFO庫存: {backup_data['summary']['total_fifo_inventories']}")
        print(f"   - 記帳記錄: {backup_data['summary']['total_ledger_entries']}")
        print(f"   - 現金日誌: {backup_data['summary']['total_cash_logs']}")
        print(f"   - 總帳戶餘額: {backup_data['summary']['total_account_balance']}")
        print(f"   - 總應收帳款: {backup_data['summary']['total_receivables']}")
        
        print(f"\n💡 備份文件已保存，現在可以安全地運行清空腳本了！")
        
except Exception as e:
    print(f"❌ 備份失敗: {e}")
    import traceback
    traceback.print_exc()
