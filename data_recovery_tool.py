#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據修復工具 - 修復因刪除售出訂單導致的數據不一致問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import FIFOInventory, PurchaseRecord, SalesRecord, CashAccount, Customer, LedgerEntry, CashLog
from sqlalchemy import func, and_
from datetime import datetime
import traceback

class DataRecoveryTool:
    def __init__(self):
        self.app = app
        self.db = db
        
    def run_recovery(self):
        """執行完整的數據修復流程"""
        print("🔧 開始執行數據修復流程...")
        print("=" * 60)
        
        try:
            with self.app.app_context():
                # 1. 修復庫存數據
                self.fix_inventory_data()
                
                # 2. 修復現金帳戶餘額
                self.fix_cash_account_balances()
                
                # 3. 修復客戶應收帳款
                self.fix_customer_receivables()
                
                # 4. 驗證數據一致性
                self.validate_data_consistency()
                
                print("\n✅ 數據修復完成！")
                
        except Exception as e:
            print(f"❌ 數據修復過程中發生錯誤: {e}")
            traceback.print_exc()
    
    def fix_inventory_data(self):
        """修復庫存數據"""
        print("\n📦 修復庫存數據...")
        
        try:
            # 重新計算所有庫存的已出帳數量
            inventories = FIFOInventory.query.filter_by(is_active=True).all()
            
            for inventory in inventories:
                # 計算實際的已出帳數量
                actual_issued = SalesRecord.query.filter(
                    and_(
                        SalesRecord.inventory_batch_id == inventory.id,
                        SalesRecord.is_active == True
                    )
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                # 更新庫存記錄
                inventory.issued_rmb = actual_issued
                inventory.remaining_rmb = inventory.original_rmb - actual_issued
                
                # 如果剩餘數量為0，標記為已出清
                if inventory.remaining_rmb <= 0:
                    inventory.is_active = False
                
                print(f"   庫存批次 {inventory.id}: 原始 {inventory.original_rmb}, 已出帳 {actual_issued}, 剩餘 {inventory.remaining_rmb}")
            
            self.db.session.commit()
            print("   ✅ 庫存數據修復完成")
            
        except Exception as e:
            print(f"   ❌ 庫存數據修復失敗: {e}")
            self.db.session.rollback()
            raise
    
    def fix_cash_account_balances(self):
        """修復現金帳戶餘額"""
        print("\n💰 修復現金帳戶餘額...")
        
        try:
            # 獲取所有現金帳戶
            cash_accounts = CashAccount.query.filter_by(is_active=True).all()
            
            for account in cash_accounts:
                original_balance = account.balance
                
                if account.currency == "TWD":
                    # 重新計算 TWD 帳戶餘額
                    # 基於買入記錄的出款
                    payment_amount = PurchaseRecord.query.filter(
                        and_(
                            PurchaseRecord.payment_account_id == account.id,
                            PurchaseRecord.is_active == True
                        )
                    ).with_entities(func.sum(PurchaseRecord.twd_cost)).scalar() or 0
                    
                    # 基於其他記帳記錄
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
                    
                    # 基於現金日誌
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
                    
                    # 計算新餘額：初始餘額 - 出款 - 提款/轉出/刷卡 + 存款/轉入/銷帳
                    new_balance = (account.initial_balance or 0) - payment_amount - ledger_debits - cash_debits + ledger_credits + cash_credits
                    
                elif account.currency == "RMB":
                    # 重新計算 RMB 帳戶餘額
                    # 基於買入記錄的入款
                    deposit_amount = PurchaseRecord.query.filter(
                        and_(
                            PurchaseRecord.deposit_account_id == account.id,
                            PurchaseRecord.is_active == True
                        )
                    ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                    
                    # 基於銷售記錄的出款
                    sales_amount = SalesRecord.query.filter(
                        and_(
                            SalesRecord.rmb_account_id == account.id,
                            SalesRecord.is_active == True
                        )
                    ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                    
                    # 基於其他記帳記錄
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
                    
                    # 計算新餘額：初始餘額 + 買入入款 - 銷售出款 - 提款/轉出 + 存款/轉入
                    new_balance = (account.initial_balance or 0) + deposit_amount - sales_amount - ledger_debits + ledger_credits
                
                # 更新帳戶餘額
                account.balance = new_balance
                
                print(f"   帳戶 {account.account_name} ({account.currency}): {original_balance} -> {new_balance}")
            
            self.db.session.commit()
            print("   ✅ 現金帳戶餘額修復完成")
            
        except Exception as e:
            print(f"   ❌ 現金帳戶餘額修復失敗: {e}")
            self.db.session.rollback()
            raise
    
    def fix_customer_receivables(self):
        """修復客戶應收帳款"""
        print("\n📋 修復客戶應收帳款...")
        
        try:
            # 獲取所有客戶
            customers = Customer.query.filter_by(is_active=True).all()
            
            for customer in customers:
                # 重新計算應收帳款
                total_receivables = SalesRecord.query.filter(
                    and_(
                        SalesRecord.customer_id == customer.id,
                        SalesRecord.is_active == True
                    )
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                # 計算已收到的款項（銷帳記錄）
                received_amount = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.customer_id == customer.id,
                        LedgerEntry.entry_type == 'SETTLEMENT',
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                # 計算應收帳款餘額
                receivables_balance = total_receivables - received_amount
                
                # 更新客戶記錄
                customer.total_receivables_twd = receivables_balance
                
                print(f"   客戶 {customer.name}: 總銷售 {total_receivables}, 已收款 {received_amount}, 應收餘額 {receivables_balance}")
            
            self.db.session.commit()
            print("   ✅ 客戶應收帳款修復完成")
            
        except Exception as e:
            print(f"   ❌ 客戶應收帳款修復失敗: {e}")
            self.db.session.rollback()
            raise
    
    def validate_data_consistency(self):
        """驗證數據一致性"""
        print("\n🔍 驗證數據一致性...")
        
        try:
            # 1. 驗證庫存總量
            total_original_rmb = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
            total_issued_rmb = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
            total_remaining_rmb = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
            
            print(f"   庫存總量驗證:")
            print(f"     原始總量: {total_original_rmb}")
            print(f"     已出帳總量: {total_issued_rmb}")
            print(f"     剩餘總量: {total_remaining_rmb}")
            print(f"     一致性檢查: {'✅' if abs(total_original_rmb - total_issued_rmb - total_remaining_rmb) < 0.01 else '❌'}")
            
            # 2. 驗證現金帳戶總餘額
            total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
            total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
            
            print(f"   現金帳戶總餘額:")
            print(f"     總 TWD: {total_twd}")
            print(f"     總 RMB: {total_rmb}")
            
            # 3. 驗證應收帳款總額
            total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
            print(f"   應收帳款總額: {total_receivables}")
            
            print("   ✅ 數據一致性驗證完成")
            
        except Exception as e:
            print(f"   ❌ 數據一致性驗證失敗: {e}")
            raise
    
    def show_current_status(self):
        """顯示當前數據狀態"""
        print("\n📊 當前數據狀態...")
        
        try:
            with self.app.app_context():
                # 庫存狀態
                active_inventories = FIFOInventory.query.filter_by(is_active=True).count()
                total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
                total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
                
                print(f"   庫存狀態: {active_inventories} 個活躍批次")
                print(f"     原始總量: {total_original}")
                print(f"     剩餘總量: {total_remaining}")
                
                # 現金帳戶狀態
                twd_accounts = CashAccount.query.filter_by(currency="TWD", is_active=True).count()
                rmb_accounts = CashAccount.query.filter_by(currency="RMB", is_active=True).count()
                total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
                total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
                
                print(f"   現金帳戶: {twd_accounts} 個 TWD 帳戶, {rmb_accounts} 個 RMB 帳戶")
                print(f"     總 TWD: {total_twd}")
                print(f"     總 RMB: {total_rmb}")
                
                # 客戶狀態
                active_customers = Customer.query.filter_by(is_active=True).count()
                total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
                
                print(f"   客戶狀態: {active_customers} 個活躍客戶")
                print(f"     應收帳款總額: {total_receivables}")
                
        except Exception as e:
            print(f"   ❌ 無法獲取當前狀態: {e}")

def main():
    """主函數"""
    print("=" * 60)
    print("🔧 數據修復工具")
    print("=" * 60)
    print("此工具將修復因刪除售出訂單導致的數據不一致問題")
    print("包括：庫存數據、現金帳戶餘額、客戶應收帳款")
    print("=" * 60)
    
    # 顯示當前狀態
    tool = DataRecoveryTool()
    tool.show_current_status()
    
    # 詢問用戶是否繼續
    response = input("\n是否繼續執行數據修復？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ 用戶取消操作")
        return
    
    # 執行修復
    tool.run_recovery()
    
    # 顯示修復後狀態
    print("\n" + "=" * 60)
    print("🔍 修復後數據狀態")
    print("=" * 60)
    tool.show_current_status()

if __name__ == "__main__":
    main()
