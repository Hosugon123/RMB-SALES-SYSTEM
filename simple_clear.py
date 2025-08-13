#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化數據清空腳本 - 準備上線部署
只清空交易記錄，保留系統基礎結構
"""

import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    # 只導入實際存在的模型類
    from app import (
        PurchaseRecord, SalesRecord, CardPurchase, LedgerEntry, CashLog,
        FIFOInventory, FIFOSalesAllocation, CashAccount, Customer
    )
    
    print("✅ 模型導入成功")
    print("🚨 簡化數據清空 - 準備上線部署")
    print("=" * 50)
    
    with app.app_context():
        print("🔄 開始清空數據...")
        
        # 1. 清空FIFO銷售分配
        print("1. 清空FIFO銷售分配...")
        db.session.execute(db.delete(FIFOSalesAllocation))
        
        # 2. 清空FIFO庫存
        print("2. 清空FIFO庫存...")
        db.session.execute(db.delete(FIFOInventory))
        
        # 3. 清空銷售記錄
        print("3. 清空銷售記錄...")
        db.session.execute(db.delete(SalesRecord))
        
        # 4. 清空買入記錄
        print("4. 清空買入記錄...")
        db.session.execute(db.delete(PurchaseRecord))
        
        # 5. 清空刷卡記錄
        print("5. 清空刷卡記錄...")
        db.session.execute(db.delete(CardPurchase))
        
        # 6. 清空記帳記錄
        print("6. 清空記帳記錄...")
        db.session.execute(db.delete(LedgerEntry))
        
        # 7. 清空現金日誌
        print("7. 清空現金日誌...")
        db.session.execute(db.delete(CashLog))
        
        # 8. 重置所有帳戶餘額為0
        print("8. 重置帳戶餘額...")
        db.session.execute(db.update(CashAccount).values(balance=0.0))
        
        # 9. 重置客戶應收帳款為0
        print("9. 重置應收帳款...")
        db.session.execute(db.update(Customer).values(total_receivables_twd=0.0))
        
        # 提交更改
        print("💾 提交數據庫更改...")
        db.session.commit()
        
        print("✅ 數據清空完成！系統已準備好上線部署")
        
        # 驗證結果
        print("\n🔍 驗證清空結果...")
        remaining_purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        remaining_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        remaining_fifo = db.session.execute(db.select(FIFOInventory)).scalars().all()
        
        print(f"   📊 剩餘買入記錄: {len(remaining_purchases)}")
        print(f"   📊 剩餘銷售記錄: {len(remaining_sales)}")
        print(f"   📊 剩餘FIFO庫存: {len(remaining_fifo)}")
        
except Exception as e:
    print(f"❌ 清空數據失敗: {e}")
    import traceback
    traceback.print_exc()
