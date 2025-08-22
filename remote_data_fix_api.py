#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遠程數據修復 API - 可以通過網頁調用來修復部署服務器上的數據庫
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import FIFOInventory, PurchaseRecord, SalesRecord, CashAccount, Customer, LedgerEntry, CashLog
from sqlalchemy import func, and_
import traceback
from datetime import datetime
import json

# 添加新的路由到現有的 Flask 應用
@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    """遠程數據修復 API 端點"""
    try:
        # 檢查是否有管理員權限（這裡可以根據您的權限系統調整）
        # 例如檢查 session 或 token
        
        print("🔧 開始遠程數據修復...")
        
        # 1. 修復庫存數據
        print("📦 修復庫存數據...")
        inventories = FIFOInventory.query.filter_by(is_active=True).all()
        
        inventory_fixes = []
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
            
            inventory_fixes.append({
                "batch_id": inventory.id,
                "original": inventory.original_rmb,
                "old_issued": old_issued,
                "new_issued": actual_issued,
                "old_remaining": old_remaining,
                "new_remaining": inventory.remaining_rmb,
                "is_active": inventory.is_active
            })
        
        # 2. 修復現金帳戶餘額
        print("💰 修復現金帳戶餘額...")
        cash_accounts = CashAccount.query.filter_by(is_active=True).all()
        
        account_fixes = []
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
            
            account_fixes.append({
                "account_id": account.id,
                "account_name": account.account_name,
                "currency": account.currency,
                "old_balance": old_balance,
                "new_balance": new_balance
            })
        
        # 3. 修復客戶應收帳款
        print("📋 修復客戶應收帳款...")
        customers = Customer.query.filter_by(is_active=True).all()
        
        customer_fixes = []
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
            
            customer_fixes.append({
                "customer_id": customer.id,
                "customer_name": customer.name,
                "old_receivables": old_receivables,
                "new_receivables": receivables_balance,
                "total_sales": total_sales,
                "received_amount": received_amount
            })
        
        # 提交所有更改
        db.session.commit()
        
        # 4. 驗證修復結果
        total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
        total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
        total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        
        total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        print("✅ 遠程數據修復完成！")
        
        return jsonify({
            "status": "success",
            "message": "數據修復完成",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "inventory_batches_fixed": len(inventory_fixes),
                "cash_accounts_fixed": len(account_fixes),
                "customers_fixed": len(customer_fixes)
            },
            "final_status": {
                "inventory": {
                    "total_original": total_original,
                    "total_issued": total_issued,
                    "total_remaining": total_remaining
                },
                "cash_accounts": {
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "receivables": total_receivables
            },
            "details": {
                "inventory_fixes": inventory_fixes,
                "account_fixes": account_fixes,
                "customer_fixes": customer_fixes
            }
        })
        
    except Exception as e:
        print(f"❌ 遠程數據修復失敗: {e}")
        traceback.print_exc()
        db.session.rollback()
        
        return jsonify({
            "status": "error",
            "message": f"數據修復失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# 添加狀態檢查 API
@app.route("/api/admin/data-status", methods=["GET"])
def get_data_status():
    """獲取當前數據狀態"""
    try:
        # 庫存狀態
        active_inventories = FIFOInventory.query.filter_by(is_active=True).count()
        total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
        total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
        
        # 現金帳戶狀態
        twd_accounts = CashAccount.query.filter_by(currency="TWD", is_active=True).count()
        rmb_accounts = CashAccount.query.filter_by(currency="RMB", is_active=True).count()
        total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        # 客戶狀態
        active_customers = Customer.query.filter_by(is_active=True).count()
        total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "inventory": {
                    "active_batches": active_inventories,
                    "total_original": total_original,
                    "total_remaining": total_remaining,
                    "total_issued": total_issued,
                    "consistency_check": abs(total_original - total_issued - total_remaining) < 0.01
                },
                "cash_accounts": {
                    "twd_accounts": twd_accounts,
                    "rmb_accounts": rmb_accounts,
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "customers": {
                    "active_customers": active_customers,
                    "total_receivables": total_receivables
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"獲取數據狀態失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    print("🔧 遠程數據修復 API 已添加到 Flask 應用")
    print("您可以通過以下端點調用：")
    print("  - POST /api/admin/data-recovery  - 執行數據修復")
    print("  - GET  /api/admin/data-status    - 檢查數據狀態")
