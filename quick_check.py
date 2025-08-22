#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速檢查腳本
"""

import os
import sys

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import CashAccount, FIFOInventory, FIFOSalesAllocation
    
    def quick_check():
        with app.app_context():
            print("🔍 快速檢查開始...")
            
            # 檢查RMB帳戶
            rmb_accounts = db.session.execute(
                db.select(CashAccount).filter_by(currency="RMB")
            ).scalars().all()
            
            print(f"📊 找到 {len(rmb_accounts)} 個RMB帳戶")
            total_rmb = 0
            for acc in rmb_accounts:
                print(f"   {acc.name}: ¥{acc.balance:,.2f}")
                total_rmb += acc.balance
            
            print(f"   總計: ¥{total_rmb:,.2f}")
            
            # 檢查FIFO庫存
            fifo_inventories = db.session.execute(
                db.select(FIFOInventory)
            ).scalars().all()
            
            print(f"\n📦 找到 {len(fifo_inventories)} 個FIFO庫存記錄")
            total_fifo = 0
            for inv in fifo_inventories:
                print(f"   批次 {inv.id}: 剩餘 ¥{inv.remaining_rmb:,.2f}")
                total_fifo += inv.remaining_rmb
            
            print(f"   總計剩餘: ¥{total_fifo:,.2f}")
            
            # 檢查差異
            diff = total_rmb - total_fifo
            print(f"\n🔍 差異分析:")
            print(f"   帳戶餘額: ¥{total_rmb:,.2f}")
            print(f"   庫存剩餘: ¥{total_fifo:,.2f}")
            print(f"   差異: ¥{diff:,.2f}")
            
            if abs(diff) < 0.01:
                print("   ✅ 數據一致！")
            else:
                print("   ❌ 數據不一致！")
    
    if __name__ == "__main__":
        quick_check()
        
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
