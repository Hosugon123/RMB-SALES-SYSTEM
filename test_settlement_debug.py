#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
銷帳功能調試腳本
檢查資料庫狀態和銷帳邏輯
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Customer, CashAccount, LedgerEntry, CashLog
from datetime import datetime

def debug_settlement():
    """調試銷帳功能"""
    with app.app_context():
        print("🔍 開始調試銷帳功能...")
        
        # 1. 檢查客戶狀態
        print("\n📋 客戶狀態檢查:")
        customers = Customer.query.all()
        for customer in customers:
            print(f"客戶: {customer.name} (ID: {customer.id})")
            print(f"  應收帳款: NT$ {customer.total_receivables_twd:,.2f}")
            print(f"  創建時間: {customer.created_at}")
            print(f"  更新時間: {customer.updated_at if hasattr(customer, 'updated_at') else 'N/A'}")
        
        # 2. 檢查現金帳戶狀態
        print("\n💰 現金帳戶狀態檢查:")
        accounts = CashAccount.query.all()
        for account in accounts:
            print(f"帳戶: {account.name} (ID: {account.id}, 幣別: {account.currency})")
            print(f"  餘額: {account.balance:,.2f}")
            print(f"  持有人: {account.holder.name if account.holder else 'N/A'}")
        
        # 3. 檢查最近的 LedgerEntry 記錄
        print("\n📝 最近的 LedgerEntry 記錄:")
        recent_entries = LedgerEntry.query.order_by(LedgerEntry.entry_date.desc()).limit(5).all()
        for entry in recent_entries:
            print(f"記錄: {entry.entry_type} (ID: {entry.id})")
            print(f"  金額: {entry.amount:,.2f}")
            print(f"  帳戶ID: {entry.account_id}")
            print(f"  描述: {entry.description}")
            print(f"  時間: {entry.entry_date}")
        
        # 4. 檢查最近的 CashLog 記錄
        print("\n💳 最近的 CashLog 記錄:")
        recent_logs = CashLog.query.order_by(CashLog.time.desc()).limit(5).all()
        for log in recent_logs:
            print(f"記錄: {log.type} (ID: {log.id})")
            print(f"  金額: {log.amount:,.2f}")
            print(f"  描述: {log.description}")
            print(f"  時間: {log.time}")
        
        # 5. 檢查資料庫連接狀態
        print("\n🔌 資料庫連接狀態:")
        try:
            # 測試簡單查詢
            result = db.session.execute("SELECT 1").scalar()
            print(f"  資料庫連接: ✅ 正常 (測試查詢結果: {result})")
        except Exception as e:
            print(f"  資料庫連接: ❌ 錯誤 - {e}")
        
        # 6. 檢查事務狀態
        print("\n🔄 事務狀態檢查:")
        try:
            # 檢查是否有未提交的事務
            db.session.execute("SELECT txid_current()").scalar()
            print("  事務狀態: ✅ 正常")
        except Exception as e:
            print(f"  事務狀態: ❌ 錯誤 - {e}")

if __name__ == "__main__":
    debug_settlement()
