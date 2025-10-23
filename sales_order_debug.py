#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售出訂單建立檢查機制
用於診斷售出訂單建立過程中的問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import SalesRecord, Customer, CashAccount, LedgerEntry
from datetime import datetime, date

def check_sales_order_creation():
    """檢查售出訂單建立過程"""
    print("🔍 開始檢查售出訂單建立機制...")
    
    with app.app_context():
        try:
            # 1. 檢查最新的售出記錄
            latest_sales = db.session.execute(
                db.select(SalesRecord)
                .order_by(SalesRecord.created_at.desc())
                .limit(5)
            ).scalars().all()
            
            print(f"📊 最新5筆售出記錄:")
            for sale in latest_sales:
                print(f"  ID: {sale.id}")
                print(f"  客戶: {sale.customer.name if sale.customer else 'N/A'}")
                print(f"  RMB金額: {sale.rmb_amount}")
                print(f"  台幣金額: {sale.twd_amount}")
                print(f"  匯率: {sale.exchange_rate}")
                print(f"  是否結清: {sale.is_settled}")
                print(f"  RMB帳戶: {sale.rmb_account.name if sale.rmb_account else 'N/A'}")
                print(f"  操作者: {sale.operator.username if sale.operator else 'N/A'}")
                print(f"  建立時間: {sale.created_at}")
                print(f"  ---")
            
            # 2. 檢查未結清的售出記錄
            unsettled_sales = db.session.execute(
                db.select(SalesRecord)
                .filter_by(is_settled=False)
                .order_by(SalesRecord.created_at.desc())
                .limit(10)
            ).scalars().all()
            
            print(f"📋 未結清的售出記錄 ({len(unsettled_sales)} 筆):")
            for sale in unsettled_sales:
                print(f"  ID: {sale.id} - {sale.customer.name if sale.customer else 'N/A'} - RMB {sale.rmb_amount} - 建立時間: {sale.created_at}")
            
            # 3. 檢查利潤記錄
            latest_profit_entries = db.session.execute(
                db.select(LedgerEntry)
                .filter(
                    (LedgerEntry.description.like("%售出利潤%")) |
                    (LedgerEntry.entry_type == "PROFIT_EARNED")
                )
                .order_by(LedgerEntry.entry_date.desc())
                .limit(5)
            ).scalars().all()
            
            print(f"💰 最新5筆利潤記錄:")
            for entry in latest_profit_entries:
                print(f"  ID: {entry.id}")
                print(f"  描述: {entry.description}")
                print(f"  金額: {entry.amount}")
                print(f"  類型: {entry.entry_type}")
                print(f"  時間: {entry.entry_date}")
                print(f"  ---")
            
            # 4. 檢查資料庫約束
            print(f"🔧 檢查資料庫約束...")
            
            # 檢查是否有NULL的rmb_account_id
            null_rmb_account = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.rmb_account_id.is_(None))
            ).scalars().all()
            
            if null_rmb_account:
                print(f"❌ 發現 {len(null_rmb_account)} 筆售出記錄缺少rmb_account_id:")
                for sale in null_rmb_account:
                    print(f"  ID: {sale.id} - 客戶: {sale.customer.name if sale.customer else 'N/A'}")
            else:
                print(f"✅ 所有售出記錄都有rmb_account_id")
            
            # 檢查是否有NULL的is_settled
            null_is_settled = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.is_settled.is_(None))
            ).scalars().all()
            
            if null_is_settled:
                print(f"❌ 發現 {len(null_is_settled)} 筆售出記錄缺少is_settled:")
                for sale in null_is_settled:
                    print(f"  ID: {sale.id} - 客戶: {sale.customer.name if sale.customer else 'N/A'}")
            else:
                print(f"✅ 所有售出記錄都有is_settled設置")
            
            # 5. 檢查客戶和帳戶關聯
            print(f"🔗 檢查關聯完整性...")
            
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
            print(f"❌ 檢查過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

def test_sales_order_creation():
    """測試售出訂單建立過程"""
    print("\n🧪 開始測試售出訂單建立...")
    
    with app.app_context():
        try:
            # 模擬表單數據
            test_data = {
                'customer_name': '測試客戶',
                'rmb_sell_amount': '1000.0',
                'exchange_rate': '4.5',
                'order_date': '2025-10-23',
                'rmb_account_id': '1'  # 假設帳戶ID為1
            }
            
            print(f"📝 測試數據: {test_data}")
            
            # 檢查客戶是否存在
            customer = Customer.query.filter_by(name=test_data['customer_name']).first()
            if not customer:
                print(f"⚠️ 測試客戶不存在，將創建新客戶")
                customer = Customer(name=test_data['customer_name'], is_active=True)
                db.session.add(customer)
                db.session.flush()
                print(f"✅ 創建測試客戶: ID {customer.id}")
            else:
                print(f"✅ 找到測試客戶: ID {customer.id}")
            
            # 檢查RMB帳戶是否存在
            rmb_account = db.session.get(CashAccount, int(test_data['rmb_account_id']))
            if not rmb_account:
                print(f"❌ 找不到RMB帳戶 ID {test_data['rmb_account_id']}")
                return
            else:
                print(f"✅ 找到RMB帳戶: {rmb_account.name}")
            
            # 模擬創建售出記錄
            rmb_amount = float(test_data['rmb_sell_amount'])
            exchange_rate = float(test_data['exchange_rate'])
            twd_amount = rmb_amount * exchange_rate
            
            print(f"💰 計算結果: RMB {rmb_amount} × {exchange_rate} = TWD {twd_amount}")
            
            # 創建測試售出記錄
            test_sale = SalesRecord(
                customer_id=customer.id,
                rmb_account_id=rmb_account.id,
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_amount=twd_amount,
                sale_date=date.fromisoformat(test_data['order_date']),
                status="PENDING",
                is_settled=False,
                operator_id=1  # 假設操作者ID為1
            )
            
            print(f"📋 創建測試售出記錄:")
            print(f"  客戶ID: {test_sale.customer_id}")
            print(f"  RMB帳戶ID: {test_sale.rmb_account_id}")
            print(f"  RMB金額: {test_sale.rmb_amount}")
            print(f"  台幣金額: {test_sale.twd_amount}")
            print(f"  是否結清: {test_sale.is_settled}")
            
            # 添加到資料庫
            db.session.add(test_sale)
            db.session.flush()
            
            print(f"✅ 測試售出記錄已創建，ID: {test_sale.id}")
            
            # 檢查是否能在未結清查詢中找到
            found_unsettled = db.session.execute(
                db.select(SalesRecord)
                .filter_by(is_settled=False, id=test_sale.id)
            ).scalar_one_or_none()
            
            if found_unsettled:
                print(f"✅ 測試記錄在未結清查詢中找到")
            else:
                print(f"❌ 測試記錄在未結清查詢中找不到")
            
            # 清理測試數據
            db.session.delete(test_sale)
            db.session.commit()
            print(f"🧹 測試數據已清理")
            
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    check_sales_order_creation()
    test_sales_order_creation()
