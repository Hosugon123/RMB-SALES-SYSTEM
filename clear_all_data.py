#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據清空腳本 - 準備上線部署
清空所有交易記錄和帳戶金額，保留系統基礎結構
"""

import sys
import os
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    # 從app.py導入模型類
    from app import (
        # 交易記錄相關
        PurchaseRecord, SalesRecord, CardPurchase, LedgerEntry, CashLog,
        # FIFO相關
        FIFOInventory, FIFOSalesAllocation,
        # 基礎結構（保留）
        User, Holder, CashAccount, Customer, Channel, PaymentAccount, DepositAccount
    )
    
    print("✅ 模型導入成功")
    print("=" * 60)
    print("🚨 數據清空腳本 - 準備上線部署")
    print("=" * 60)
    print("⚠️  警告：此操作將清空所有交易數據！")
    print("📋 將被清空的數據：")
    print("   - 買入記錄")
    print("   - 銷售記錄") 
    print("   - 刷卡記錄")
    print("   - 記帳記錄")
    print("   - 現金日誌")
    print("   - FIFO庫存")
    print("   - FIFO銷售分配")
    print()
    print("🔒 將被保留的數據：")
    print("   - 用戶帳戶")
    print("   - 資金持有人")
    print("   - 現金帳戶結構")
    print("   - 客戶資料")
    print("   - 渠道資料")
    print("   - 付款/收款帳戶")
    print()
    
    # 確認操作
    confirm = input("❓ 確認要清空所有交易數據嗎？(輸入 'YES' 確認): ")
    if confirm != "YES":
        print("❌ 操作已取消")
        sys.exit(0)
    
    with app.app_context():
        print("\n🔄 開始清空數據...")
        
        # 1. 清空FIFO銷售分配
        print("1. 清空FIFO銷售分配...")
        fifo_allocations = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
        for allocation in fifo_allocations:
            db.session.delete(allocation)
        print(f"   ✅ 已刪除 {len(fifo_allocations)} 個FIFO銷售分配")
        
        # 2. 清空FIFO庫存
        print("2. 清空FIFO庫存...")
        fifo_inventories = db.session.execute(db.select(FIFOInventory)).scalars().all()
        for inventory in fifo_inventories:
            db.session.delete(inventory)
        print(f"   ✅ 已刪除 {len(fifo_inventories)} 個FIFO庫存記錄")
        
        # 3. 清空銷售記錄
        print("3. 清空銷售記錄...")
        sales_records = db.session.execute(db.select(SalesRecord)).scalars().all()
        for sale in sales_records:
            db.session.delete(sale)
        print(f"   ✅ 已刪除 {len(sales_records)} 個銷售記錄")
        
        # 4. 清空買入記錄
        print("4. 清空買入記錄...")
        purchase_records = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        for purchase in purchase_records:
            db.session.delete(purchase)
        print(f"   ✅ 已刪除 {len(purchase_records)} 個買入記錄")
        
        # 5. 清空刷卡記錄
        print("5. 清空刷卡記錄...")
        card_purchases = db.session.execute(db.select(CardPurchase)).scalars().all()
        for card_purchase in card_purchases:
            db.session.delete(card_purchase)
        print(f"   ✅ 已刪除 {len(card_purchases)} 個刷卡記錄")
        
        # 6. 清空記帳記錄
        print("6. 清空記帳記錄...")
        ledger_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
        for entry in ledger_entries:
            db.session.delete(entry)
        print(f"   ✅ 已刪除 {len(ledger_entries)} 個記帳記錄")
        
        # 7. 清空現金日誌
        print("7. 清空現金日誌...")
        cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        for log in cash_logs:
            db.session.delete(log)
        print(f"   ✅ 已刪除 {len(cash_logs)} 個現金日誌")
        
        # 8. 重置所有帳戶餘額為0
        print("8. 重置帳戶餘額...")
        cash_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        for account in cash_accounts:
            account.balance = 0.0
        print(f"   ✅ 已重置 {len(cash_accounts)} 個帳戶餘額為0")
        
        # 9. 重置客戶應收帳款為0
        print("9. 重置客戶應收帳款...")
        customers = db.session.execute(db.select(Customer)).scalars().all()
        for customer in customers:
            customer.total_receivables_twd = 0.0
        print(f"   ✅ 已重置 {len(customers)} 個客戶應收帳款為0")
        
        # 提交所有更改
        print("\n💾 提交數據庫更改...")
        db.session.commit()
        print("   ✅ 數據庫更改已提交")
        
        # 驗證清空結果
        print("\n🔍 驗證清空結果...")
        
        remaining_purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        remaining_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        remaining_card_purchases = db.session.execute(db.select(CardPurchase)).scalars().all()
        remaining_fifo_inventories = db.session.execute(db.select(FIFOInventory)).scalars().all()
        remaining_fifo_allocations = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
        
        total_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        total_balance = sum(acc.balance for acc in total_accounts)
        
        print(f"   📊 剩餘買入記錄: {len(remaining_purchases)}")
        print(f"   📊 剩餘銷售記錄: {len(remaining_sales)}")
        print(f"   📊 剩餘刷卡記錄: {len(remaining_card_purchases)}")
        print(f"   📊 剩餘FIFO庫存: {len(remaining_fifo_inventories)}")
        print(f"   📊 剩餘FIFO分配: {len(remaining_fifo_allocations)}")
        print(f"   💰 總帳戶餘額: {total_balance}")
        
        print("\n" + "=" * 60)
        print("🎉 數據清空完成！系統已準備好上線部署")
        print("=" * 60)
        print("📝 清空摘要：")
        print(f"   - 刪除買入記錄: {len(purchase_records)}")
        print(f"   - 刪除銷售記錄: {len(sales_records)}")
        print(f"   - 刪除刷卡記錄: {len(card_purchases)}")
        print(f"   - 刪除記帳記錄: {len(ledger_entries)}")
        print(f"   - 刪除現金日誌: {len(cash_logs)}")
        print(f"   - 刪除FIFO庫存: {len(fifo_inventories)}")
        print(f"   - 刪除FIFO分配: {len(fifo_allocations)}")
        print(f"   - 重置帳戶餘額: {len(cash_accounts)}")
        print(f"   - 重置應收帳款: {len(customers)}")
        print()
        print("✅ 系統現在處於乾淨狀態，可以安全上線部署！")
        
except Exception as e:
    print(f"❌ 清空數據失敗: {e}")
    import traceback
    traceback.print_exc()
    
    # 如果發生錯誤，嘗試回滾
    try:
        with app.app_context():
            db.session.rollback()
            print("🔄 已回滾數據庫更改")
    except:
        print("⚠️  無法回滾數據庫更改")
