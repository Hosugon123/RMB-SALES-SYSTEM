#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速數據修復腳本 - 修復因刪除售出訂單導致的數據不一致問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import FIFOInventory, PurchaseRecord, SalesRecord, CashAccount, Customer, LedgerEntry, CashLog
from sqlalchemy import func, and_
import traceback

def quick_fix():
    """快速修復數據不一致問題"""
    print("🔧 開始快速數據修復...")
    print("=" * 50)
    
    try:
        with app.app_context():
            print("📦 修復庫存數據...")
            
            # 1. 重新計算所有庫存的已出帳數量和剩餘數量
            inventories = FIFOInventory.query.filter_by(is_active=True).all()
            
            for inventory in inventories:
                # 計算實際的已出帳數量（基於現有的銷售記錄）
                actual_issued = SalesRecord.query.filter(
                    and_(
                        SalesRecord.inventory_batch_id == inventory.id,
                        SalesRecord.is_active == True
                    )
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                # 更新庫存記錄
                inventory.issued_rmb = actual_issued
                inventory.remaining_rmb = inventory.original_rmb - actual_issued
                
                # 如果剩餘數量為0或負數，標記為已出清
                if inventory.remaining_rmb <= 0:
                    inventory.is_active = False
                
                print(f"   批次 {inventory.id}: 原始 {inventory.original_rmb}, 已出帳 {actual_issued}, 剩餘 {inventory.remaining_rmb}")
            
            print("💰 修復現金帳戶餘額...")
            
            # 2. 重新計算現金帳戶餘額
            cash_accounts = CashAccount.query.filter_by(is_active=True).all()
            
            for account in cash_accounts:
                if account.currency == "TWD":
                    # TWD 帳戶：基於買入記錄的出款和其他交易
                    payment_amount = PurchaseRecord.query.filter(
                        and_(
                            PurchaseRecord.payment_account_id == account.id,
                            PurchaseRecord.is_active == True
                        )
                    ).with_entities(func.sum(PurchaseRecord.twd_cost)).scalar() or 0
                    
                    # 其他記帳記錄
                    ledger_debits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT', 'CARD_PURCHASE']),
                            LedgerEntry.is_active == True
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    ledger_credits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN', 'SETTLEMENT']),
                            LedgerEntry.is_active == True
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    # 現金日誌
                    cash_debits = CashLog.query.filter(
                        and_(
                            CashLog.account_id == account.id,
                            CashLog.type.in_(['WITHDRAWAL', 'CARD_PURCHASE']),
                            CashLog.is_active == True
                        )
                    ).with_entities(func.sum(CashLog.amount)).scalar() or 0
                    
                    cash_credits = CashLog.query.filter(
                        and_(
                            CashLog.account_id == account.id,
                            CashLog.type.in_(['DEPOSIT', 'SETTLEMENT']),
                            CashLog.is_active == True
                        )
                    ).with_entities(func.sum(CashLog.amount)).scalar() or 0
                    
                    new_balance = (account.initial_balance or 0) - payment_amount - ledger_debits - cash_debits + ledger_credits + cash_credits
                    
                elif account.currency == "RMB":
                    # RMB 帳戶：基於買入記錄的入款和銷售記錄的出款
                    deposit_amount = PurchaseRecord.query.filter(
                        and_(
                            PurchaseRecord.deposit_account_id == account.id,
                            PurchaseRecord.is_active == True
                        )
                    ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                    
                    sales_amount = SalesRecord.query.filter(
                        and_(
                            SalesRecord.rmb_account_id == account.id,
                            SalesRecord.is_active == True
                        )
                    ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                    
                    # 其他記帳記錄
                    ledger_debits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT']),
                            LedgerEntry.is_active == True
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    ledger_credits = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.account_id == account.id,
                            LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN']),
                            LedgerEntry.is_active == True
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
                    new_balance = (account.initial_balance or 0) + deposit_amount - sales_amount - ledger_debits + ledger_credits
                
                account.balance = new_balance
                print(f"   帳戶 {account.account_name} ({account.currency}): {new_balance}")
            
            print("📋 修復客戶應收帳款...")
            
            # 3. 重新計算客戶應收帳款
            customers = Customer.query.filter_by(is_active=True).all()
            
            for customer in customers:
                # 總銷售金額
                total_sales = SalesRecord.query.filter(
                    and_(
                        SalesRecord.customer_id == customer.id,
                        SalesRecord.is_active == True
                    )
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                # 已收款金額
                received_amount = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.customer_id == customer.id,
                        LedgerEntry.entry_type == 'SETTLEMENT',
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                # 應收帳款餘額
                receivables_balance = total_sales - received_amount
                customer.total_receivables_twd = receivables_balance
                
                print(f"   客戶 {customer.name}: 總銷售 {total_sales}, 已收款 {received_amount}, 應收餘額 {receivables_balance}")
            
            # 提交所有更改
            db.session.commit()
            print("\n✅ 數據修復完成！")
            
            # 顯示修復後的狀態
            print("\n📊 修復後數據狀態:")
            total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
            total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
            total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
            
            print(f"   庫存: 原始 {total_original}, 已出帳 {total_issued}, 剩餘 {total_remaining}")
            
            total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
            total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
            
            print(f"   現金: 總 TWD {total_twd}, 總 RMB {total_rmb}")
            
            total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
            print(f"   應收帳款: {total_receivables}")
            
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")
        traceback.print_exc()
        db.session.rollback()

if __name__ == "__main__":
    print("🔧 快速數據修復工具")
    print("此工具將修復因刪除售出訂單導致的數據不一致問題")
    print("包括：庫存數據、現金帳戶餘額、客戶應收帳款")
    print("=" * 50)
    
    response = input("是否繼續執行數據修復？(y/N): ").strip().lower()
    if response in ['y', 'yes']:
        quick_fix()
    else:
        print("❌ 用戶取消操作")
