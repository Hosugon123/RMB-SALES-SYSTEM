#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render 數據修復腳本 - 專門為 Render 部署設計
"""

import os
import sys
import traceback
from datetime import datetime

# 添加項目路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app import app, db
    from models import FIFOInventory, PurchaseRecord, SalesRecord, CashAccount, Customer, LedgerEntry, CashLog
    from sqlalchemy import func, and_
    print("✅ 成功導入所需模組")
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保在正確的項目目錄中執行此腳本")
    sys.exit(1)

def render_data_fix():
    """Render 環境下的數據修復主函數"""
    print("🔧 開始 Render 數據修復...")
    print(f"⏰ 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 修復庫存數據
        print("\n📦 修復庫存數據...")
        inventory_fixes = fix_inventory_data()
        
        # 2. 修復現金帳戶餘額
        print("\n💰 修復現金帳戶餘額...")
        account_fixes = fix_cash_account_balances()
        
        # 3. 修復客戶應收帳款
        print("\n📋 修復客戶應收帳款...")
        customer_fixes = fix_customer_receivables()
        
        # 提交所有更改
        db.session.commit()
        print("✅ 所有數據已成功提交到數據庫")
        
        # 4. 驗證修復結果
        print("\n🔍 驗證修復結果...")
        final_status = validate_final_status()
        
        # 5. 生成修復報告
        report = generate_recovery_report(inventory_fixes, account_fixes, customer_fixes, final_status)
        
        print("\n" + "="*50)
        print("🎉 數據修復完成！")
        print("="*50)
        print(f"📊 修復摘要:")
        print(f"   - 庫存批次: {len(inventory_fixes)} 個")
        print(f"   - 現金帳戶: {len(account_fixes)} 個")
        print(f"   - 客戶: {len(customer_fixes)} 個")
        print(f"⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return report
        
    except Exception as e:
        print(f"\n❌ 數據修復失敗: {e}")
        traceback.print_exc()
        db.session.rollback()
        print("🔄 已回滾所有數據庫更改")
        return None

def fix_inventory_data():
    """修復庫存數據"""
    inventories = FIFOInventory.query.filter_by(is_active=True).all()
    fixes = []
    
    for inventory in inventories:
        # 計算實際的已出帳數量
        actual_issued = SalesRecord.query.filter(
            and_(
                SalesRecord.inventory_batch_id == inventory.id,
                SalesRecord.is_active == True
            )
        ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
        
        # 更新庫存記錄
        old_issued = inventory.issued_rmb
        old_remaining = inventory.remaining_rmb
        
        inventory.issued_rmb = actual_issued
        inventory.remaining_rmb = inventory.original_rmb - actual_issued
        
        # 如果剩餘數量為0，標記為已出清
        if inventory.remaining_rmb <= 0:
            inventory.is_active = False
        
        fixes.append({
            "batch_id": inventory.id,
            "original": inventory.original_rmb,
            "old_issued": old_issued,
            "new_issued": actual_issued,
            "old_remaining": old_remaining,
            "new_remaining": inventory.remaining_rmb,
            "is_active": inventory.is_active
        })
        
        print(f"   - 批次 {inventory.id}: {old_issued} → {actual_issued} (已出帳), {old_remaining} → {inventory.remaining_rmb} (剩餘)")
    
    return fixes

def fix_cash_account_balances():
    """修復現金帳戶餘額"""
    cash_accounts = CashAccount.query.filter_by(is_active=True).all()
    fixes = []
    
    for account in cash_accounts:
        old_balance = account.balance
        
        if account.currency == "TWD":
            # TWD 帳戶餘額計算
            payment_amount = PurchaseRecord.query.filter(
                and_(
                    PurchaseRecord.payment_account_id == account.id,
                    PurchaseRecord.is_active == True
                )
            ).with_entities(func.sum(PurchaseRecord.twd_cost)).scalar() or 0
            
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
            # RMB 帳戶餘額計算
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
        
        fixes.append({
            "account_id": account.id,
            "account_name": account.account_name,
            "currency": account.currency,
            "old_balance": old_balance,
            "new_balance": new_balance
        })
        
        print(f"   - {account.account_name} ({account.currency}): {old_balance} → {new_balance}")
    
    return fixes

def fix_customer_receivables():
    """修復客戶應收帳款"""
    customers = Customer.query.filter_by(is_active=True).all()
    fixes = []
    
    for customer in customers:
        old_receivables = customer.total_receivables_twd
        
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
        
        fixes.append({
            "customer_id": customer.id,
            "customer_name": customer.name,
            "old_receivables": old_receivables,
            "new_receivables": receivables_balance,
            "total_sales": total_sales,
            "received_amount": received_amount
        })
        
        print(f"   - {customer.name}: {old_receivables} → {receivables_balance}")
    
    return fixes

def validate_final_status():
    """驗證最終狀態"""
    # 庫存狀態
    total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
    total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
    total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
    
    # 現金帳戶狀態
    total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
    total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
    
    # 客戶狀態
    total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
    
    print(f"   📦 庫存: 原始 {total_original}, 已出帳 {total_issued}, 剩餘 {total_remaining}")
    print(f"   💰 現金: TWD {total_twd}, RMB {total_rmb}")
    print(f"   📋 應收: {total_receivables}")
    
    return {
        "inventory": {"total_original": total_original, "total_issued": total_issued, "total_remaining": total_remaining},
        "cash_accounts": {"total_twd": total_twd, "total_rmb": total_rmb},
        "receivables": total_receivables
    }

def generate_recovery_report(inventory_fixes, account_fixes, customer_fixes, final_status):
    """生成修復報告"""
    report = {
        "title": "Render 數據修復報告",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "inventory_batches_fixed": len(inventory_fixes),
            "cash_accounts_fixed": len(account_fixes),
            "customers_fixed": len(customer_fixes)
        },
        "final_status": final_status,
        "details": {
            "inventory_fixes": inventory_fixes,
            "account_fixes": account_fixes,
            "customer_fixes": customer_fixes
        }
    }
    
    # 保存報告到文件
    report_file = f"render_recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 修復報告已保存到: {report_file}")
    except Exception as e:
        print(f"⚠️ 無法保存報告文件: {e}")
    
    return report

if __name__ == "__main__":
    print("🚀 Render 數據修復工具啟動")
    print("="*50)
    
    # 檢查環境
    print(f"🌍 當前目錄: {os.getcwd()}")
    print(f"🐍 Python 版本: {sys.version}")
    print(f"📁 項目路徑: {current_dir}")
    
    # 執行修復
    result = render_data_fix()
    
    if result:
        print("\n✅ 修復完成，系統已恢復正常")
    else:
        print("\n❌ 修復失敗，請檢查錯誤日誌")
        sys.exit(1)
