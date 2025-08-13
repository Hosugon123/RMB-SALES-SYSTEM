#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速數據清空腳本 - 準備上線部署
無需確認，直接清空所有交易記錄和帳戶金額
"""

import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    # 從app.py導入模型類
    from app import (
        PurchaseRecord, SalesRecord, CardPurchase, LedgerEntry, CashLog,
        FIFOInventory, FIFOSalesAllocation, CashAccount, Customer
    )
    
    print("✅ 模型導入成功")
    print("🚨 快速數據清空 - 準備上線部署")
    print("=" * 50)
    
    with app.app_context():
        print("🔄 開始清空數據...")
        
        # 清空所有交易相關數據
        print("1. 清空FIFO銷售分配...")
        db.session.execute(db.delete(FIFOSalesAllocation))
        
        print("2. 清空FIFO庫存...")
        db.session.execute(db.delete(FIFOInventory))
        
        print("3. 清空銷售記錄...")
        db.session.execute(db.delete(SalesRecord))
        
        print("4. 清空買入記錄...")
        db.session.execute(db.delete(PurchaseRecord))
        
        print("5. 清空刷卡記錄...")
        db.session.execute(db.delete(CardPurchase))
        
        print("6. 清空記帳記錄...")
        db.session.execute(db.delete(LedgerEntry))
        
        print("7. 清空現金日誌...")
        db.session.execute(db.delete(CashLog))
        
        print("8. 重置帳戶餘額...")
        db.session.execute(db.update(CashAccount).values(balance=0.0))
        
        print("9. 重置應收帳款...")
        db.session.execute(db.update(Customer).values(total_receivables_twd=0.0))
        
        # 提交更改
        print("💾 提交數據庫更改...")
        db.session.commit()
        
        print("✅ 數據清空完成！系統已準備好上線部署")
        
except Exception as e:
    print(f"❌ 清空數據失敗: {e}")
    import traceback
    traceback.print_exc()
