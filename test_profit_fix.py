#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
利潤修復測試腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import SalesRecord, LedgerEntry
from app import FIFOService

def test_profit_calculations():
    """測試三個利潤計算方法是否一致"""
    print("🔍 測試利潤計算一致性...")
    
    with app.app_context():
        try:
            # 1. 計算儀表板利潤（FIFO方法）
            all_sales = db.session.execute(
                db.select(SalesRecord)
            ).scalars().all()
            
            dashboard_profit = 0.0
            for sale in all_sales:
                profit_info = FIFOService.calculate_profit_for_sale(sale)
                if profit_info:
                    dashboard_profit += profit_info.get('profit_twd', 0.0)
            
            # 扣除利潤提款
            profit_withdrawals = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
            ).scalars().all()
            
            total_withdrawals = sum(abs(entry.amount) for entry in profit_withdrawals)
            dashboard_profit -= total_withdrawals
            
            print(f"📊 儀表板利潤: NT$ {dashboard_profit:.2f}")
            print(f"   銷售利潤: NT$ {dashboard_profit + total_withdrawals:.2f}")
            print(f"   利潤提款: NT$ {total_withdrawals:.2f}")
            
            # 2. 計算利潤更動紀錄的最新餘額
            profit_entries = db.session.execute(
                db.select(LedgerEntry)
                .filter(
                    (LedgerEntry.entry_type == "PROFIT_WITHDRAW") |
                    (LedgerEntry.entry_type == "PROFIT_DEDUCT") |
                    (LedgerEntry.entry_type == "PROFIT_EARNED") |
                    (LedgerEntry.description.like("%利潤提款%")) |
                    (LedgerEntry.description.like("%利潤扣除%")) |
                    (LedgerEntry.description.like("%售出利潤%"))
                )
                .order_by(LedgerEntry.entry_date.asc())
            ).scalars().all()
            
            # 按時間順序累積計算
            running_balance = 0.0
            for entry in profit_entries:
                is_withdrawal = (
                    entry.entry_type == "PROFIT_WITHDRAW" or
                    entry.entry_type == "PROFIT_DEDUCT" or
                    "利潤提款" in (entry.description or "") or
                    "利潤扣除" in (entry.description or "")
                )
                
                if is_withdrawal:
                    running_balance -= abs(entry.amount)
                else:
                    running_balance += abs(entry.amount)
            
            print(f"📝 利潤更動紀錄餘額: NT$ {running_balance:.2f}")
            
            # 3. 檢查一致性
            diff = abs(dashboard_profit - running_balance)
            if diff < 0.01:
                print(f"✅ 兩個數字一致！差異: NT$ {diff:.2f}")
            else:
                print(f"❌ 數字不一致！差異: NT$ {diff:.2f}")
            
            # 4. 顯示詳細的利潤記錄
            print(f"\n📋 利潤記錄詳情:")
            for entry in profit_entries[-10:]:  # 顯示最新10筆
                is_withdrawal = (
                    entry.entry_type == "PROFIT_WITHDRAW" or
                    entry.entry_type == "PROFIT_DEDUCT" or
                    "利潤提款" in (entry.description or "") or
                    "利潤扣除" in (entry.description or "")
                )
                
                amount = -abs(entry.amount) if is_withdrawal else abs(entry.amount)
                print(f"   {entry.entry_date.strftime('%Y-%m-%d %H:%M:%S')} - {entry.description}: {amount:+.2f}")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_profit_calculations()
