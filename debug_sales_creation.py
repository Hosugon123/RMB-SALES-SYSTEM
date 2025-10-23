#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售出功能調試腳本
檢查售出記錄建立和顯示問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import SalesRecord, Customer, CashAccount, LedgerEntry
from datetime import datetime, date

def debug_sales_creation():
    """調試售出記錄建立問題"""
    print("🔍 開始調試售出記錄建立問題...")
    
    with app.app_context():
        try:
            # 1. 檢查最新的售出記錄
            latest_sales = db.session.execute(
                db.select(SalesRecord)
                .order_by(SalesRecord.created_at.desc())
                .limit(10)
            ).scalars().all()
            
            print(f"📊 最新10筆售出記錄:")
            for i, sale in enumerate(latest_sales):
                print(f"  {i+1}. ID: {sale.id}")
                print(f"     客戶: {sale.customer.name if sale.customer else 'None'}")
                print(f"     RMB帳戶: {sale.rmb_account.name if s.rmb_account else 'None'}")
                print(f"     操作者: {sale.operator.username if s.operator else 'None'}")
                print(f"     RMB金額: {sale.rmb_amount}")
                print(f"     台幣金額: {sale.twd_amount}")
                print(f"     是否結清: {sale.is_settled}")
                print(f"     建立時間: {sale.created_at}")
                print(f"     ---")
            
            # 2. 檢查未結清的售出記錄
            unsettled_sales = db.session.execute(
                db.select(SalesRecord)
                .filter_by(is_settled=False)
                .order_by(SalesRecord.created_at.desc())
                .limit(10)
            ).scalars().all()
            
            print(f"\n📋 未結清的售出記錄 ({len(unsettled_sales)} 筆):")
            for i, sale in enumerate(unsettled_sales):
                print(f"  {i+1}. ID: {sale.id} - {sale.customer.name if sale.customer else 'None'} - RMB {sale.rmb_amount} - {sale.created_at}")
            
            # 3. 檢查今天建立的售出記錄
            today = date.today()
            today_sales = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.created_at >= today)
                .order_by(SalesRecord.created_at.desc())
            ).scalars().all()
            
            print(f"\n📅 今天建立的售出記錄 ({len(today_sales)} 筆):")
            for i, sale in enumerate(today_sales):
                print(f"  {i+1}. ID: {sale.id} - {sale.customer.name if sale.customer else 'None'} - RMB {sale.rmb_amount} - {sale.created_at}")
            
            # 4. 檢查利潤記錄
            latest_profit_entries = db.session.execute(
                db.select(LedgerEntry)
                .filter(
                    (LedgerEntry.description.like("%售出利潤%")) |
                    (LedgerEntry.entry_type == "PROFIT_EARNED")
                )
                .order_by(LedgerEntry.entry_date.desc())
                .limit(10)
            ).scalars().all()
            
            print(f"\n💰 最新10筆利潤記錄:")
            for i, entry in enumerate(latest_profit_entries):
                print(f"  {i+1}. ID: {entry.id}")
                print(f"     描述: {entry.description}")
                print(f"     金額: {entry.amount}")
                print(f"     類型: {entry.entry_type}")
                print(f"     時間: {entry.entry_date}")
                print(f"     ---")
            
            # 5. 檢查資料庫約束問題
            print(f"\n🔧 檢查資料庫約束...")
            
            # 檢查是否有NULL的is_settled
            null_is_settled = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.is_settled.is_(None))
            ).scalars().all()
            
            if null_is_settled:
                print(f"❌ 發現 {len(null_is_settled)} 筆售出記錄缺少is_settled:")
                for sale in null_is_settled:
                    print(f"  ID: {sale.id} - 客戶: {sale.customer.name if sale.customer else 'None'}")
            else:
                print(f"✅ 所有售出記錄都有is_settled設置")
            
            # 檢查是否有NULL的rmb_account_id
            null_rmb_account = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.rmb_account_id.is_(None))
            ).scalars().all()
            
            if null_rmb_account:
                print(f"❌ 發現 {len(null_rmb_account)} 筆售出記錄缺少rmb_account_id:")
                for sale in null_rmb_account:
                    print(f"  ID: {sale.id} - 客戶: {sale.customer.name if sale.customer else 'None'}")
            else:
                print(f"✅ 所有售出記錄都有rmb_account_id")
            
            # 6. 檢查客戶和帳戶關聯
            print(f"\n🔗 檢查關聯完整性...")
            
            broken_customer_links = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.customer_id.isnot(None))
                .filter(~SalesRecord.customer.has())
            ).scalars().all()
            
            if broken_customer_links:
                print(f"❌ 發現 {len(broken_customer_links)} 筆售出記錄有無效的客戶關聯")
            else:
                print(f"✅ 所有售出記錄的客戶關聯都正常")
            
            broken_account_links = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.rmb_account_id.isnot(None))
                .filter(~SalesRecord.rmb_account.has())
            ).scalars().all()
            
            if broken_account_links:
                print(f"❌ 發現 {len(broken_account_links)} 筆售出記錄有無效的帳戶關聯")
            else:
                print(f"✅ 所有售出記錄的帳戶關聯都正常")
            
        except Exception as e:
            print(f"❌ 調試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_sales_creation()
