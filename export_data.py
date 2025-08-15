#!/usr/bin/env python3
"""
導出本地數據庫數據到JSON文件
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Holder, CashAccount, Customer, PurchaseRecord, SalesRecord, LedgerEntry, CashLog, Channel

def export_database():
    """導出所有數據表到JSON文件"""
    with app.app_context():
        print("🚀 開始導出數據庫數據...")
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "users": [],
            "holders": [],
            "cash_accounts": [],
            "customers": [],
            "channels": [],
            "purchase_records": [],
            "sales_records": [],
            "ledger_entries": [],
            "cash_logs": []
        }
        
        # 導出用戶
        users = db.session.execute(db.select(User)).scalars().all()
        for user in users:
            export_data["users"].append({
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "is_admin": user.is_admin,
                "is_active": user.is_active
            })
        print(f"✅ 導出 {len(users)} 個用戶")
        
        # 導出持有人
        holders = db.session.execute(db.select(Holder)).scalars().all()
        for holder in holders:
            export_data["holders"].append({
                "id": holder.id,
                "name": holder.name,
                "is_active": holder.is_active
            })
        print(f"✅ 導出 {len(holders)} 個持有人")
        
        # 導出現金帳戶
        accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        for account in accounts:
            export_data["cash_accounts"].append({
                "id": account.id,
                "name": account.name,
                "currency": account.currency,
                "balance": float(account.balance),
                "holder_id": account.holder_id
            })
        print(f"✅ 導出 {len(accounts)} 個現金帳戶")
        
        # 導出客戶
        try:
            customers = db.session.execute(db.select(Customer)).scalars().all()
            for customer in customers:
                export_data["customers"].append({
                    "id": customer.id,
                    "name": customer.name,
                    "is_active": customer.is_active,
                    "total_receivables_twd": float(customer.total_receivables_twd)
                })
            print(f"✅ 導出 {len(customers)} 個客戶")
        except Exception as e:
            print(f"⚠️ 客戶表導出失敗: {e}")
        
        # 導出渠道
        try:
            channels = db.session.execute(db.select(Channel)).scalars().all()
            for channel in channels:
                export_data["channels"].append({
                    "id": channel.id,
                    "name": channel.name,
                    "is_active": channel.is_active
                })
            print(f"✅ 導出 {len(channels)} 個渠道")
        except Exception as e:
            print(f"⚠️ 渠道表導出失敗: {e}")
        
        # 導出買入記錄
        try:
            purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
            for purchase in purchases:
                export_data["purchase_records"].append({
                    "id": purchase.id,
                    "rmb_amount": float(purchase.rmb_amount),
                    "exchange_rate": float(purchase.exchange_rate),
                    "twd_cost": float(purchase.twd_cost),
                    "channel_id": purchase.channel_id,
                    "payment_account_id": purchase.payment_account_id,
                    "deposit_account_id": purchase.deposit_account_id,
                    "operator_id": purchase.operator_id,
                    "created_at": purchase.created_at.isoformat() if purchase.created_at else None
                })
            print(f"✅ 導出 {len(purchases)} 個買入記錄")
        except Exception as e:
            print(f"⚠️ 買入記錄導出失敗: {e}")
        
        # 導出銷售記錄
        try:
            sales = db.session.execute(db.select(SalesRecord)).scalars().all()
            for sale in sales:
                export_data["sales_records"].append({
                    "id": sale.id,
                    "customer_id": sale.customer_id,
                    "rmb_account_id": sale.rmb_account_id,
                    "rmb_amount": float(sale.rmb_amount),
                    "exchange_rate": float(sale.exchange_rate),
                    "twd_amount": float(sale.twd_amount),
                    "is_settled": sale.is_settled,
                    "operator_id": sale.operator_id,
                    "created_at": sale.created_at.isoformat() if sale.created_at else None
                })
            print(f"✅ 導出 {len(sales)} 個銷售記錄")
        except Exception as e:
            print(f"⚠️ 銷售記錄導出失敗: {e}")
        
        # 導出分錄記錄
        try:
            entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
            for entry in entries:
                export_data["ledger_entries"].append({
                    "id": entry.id,
                    "account_id": entry.account_id,
                    "entry_type": entry.entry_type,
                    "amount": float(entry.amount),
                    "description": entry.description,
                    "operator_id": entry.operator_id,
                    "entry_date": entry.entry_date.isoformat() if entry.entry_date else None
                })
            print(f"✅ 導出 {len(entries)} 個分錄記錄")
        except Exception as e:
            print(f"⚠️ 分錄記錄導出失敗: {e}")
        
        # 導出現金流水記錄
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
            for log in cash_logs:
                export_data["cash_logs"].append({
                    "id": log.id,
                    "from_account_id": log.from_account_id,
                    "to_account_id": log.to_account_id,
                    "amount": float(log.amount),
                    "description": log.description,
                    "operator_id": log.operator_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            print(f"✅ 導出 {len(cash_logs)} 個現金流水記錄")
        except Exception as e:
            print(f"⚠️ 現金流水記錄導出失敗: {e}")
        
        # 寫入JSON文件
        filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"🎉 數據導出完成！文件：{filename}")
        return filename

if __name__ == "__main__":
    export_database()
