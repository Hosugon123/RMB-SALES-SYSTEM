#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
利潤計算修復腳本
統一儀表板、利潤管理和利潤更動紀錄的利潤計算邏輯
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, FIFOService
from models import SalesRecord, LedgerEntry, CashAccount
from datetime import datetime

def calculate_correct_total_profit():
    """計算正確的總利潤"""
    print("🔍 開始計算正確的總利潤...")
    
    # 1. 使用FIFO計算所有銷售記錄的利潤
    all_sales = db.session.execute(
        db.select(SalesRecord).order_by(SalesRecord.created_at.asc())
    ).scalars().all()
    
    total_profit_from_sales = 0.0
    sales_details = []
    
    for sale in all_sales:
        profit_info = FIFOService.calculate_profit_for_sale(sale)
        if profit_info:
            sale_profit = profit_info.get('profit_twd', 0.0)
            total_profit_from_sales += sale_profit
            sales_details.append({
                'id': sale.id,
                'customer': sale.customer.name if sale.customer else 'N/A',
                'twd_amount': sale.twd_amount,
                'rmb_amount': sale.rmb_amount,
                'profit': sale_profit,
                'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"銷售 {sale.id}: {sale.customer.name if sale.customer else 'N/A'} - 利潤: {sale_profit:.2f}")
    
    print(f"📊 總銷售利潤: {total_profit_from_sales:.2f}")
    
    # 2. 扣除利潤提款記錄
    profit_withdrawals = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
        .order_by(LedgerEntry.entry_date.asc())
    ).scalars().all()
    
    total_withdrawals = 0.0
    withdrawal_details = []
    
    for withdrawal in profit_withdrawals:
        withdrawal_amount = abs(withdrawal.amount)  # 提款記錄的amount是負數
        total_withdrawals += withdrawal_amount
        withdrawal_details.append({
            'id': withdrawal.id,
            'amount': withdrawal_amount,
            'description': withdrawal.description,
            'date': withdrawal.entry_date.strftime('%Y-%m-%d %H:%M:%S')
        })
        print(f"利潤提款 {withdrawal.id}: {withdrawal_amount:.2f} - {withdrawal.description}")
    
    print(f"💰 總利潤提款: {total_withdrawals:.2f}")
    
    # 3. 計算最終利潤
    final_profit = total_profit_from_sales - total_withdrawals
    print(f"✅ 最終利潤: {final_profit:.2f}")
    
    return {
        'total_profit_from_sales': total_profit_from_sales,
        'total_withdrawals': total_withdrawals,
        'final_profit': final_profit,
        'sales_details': sales_details,
        'withdrawal_details': withdrawal_details
    }

def fix_ledger_entries_profit_balance(correct_profit):
    """修復LedgerEntry中的利潤餘額記錄"""
    print("\n🔧 開始修復LedgerEntry中的利潤餘額記錄...")
    
    # 獲取所有利潤相關的記錄，按時間排序
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
    
    print(f"找到 {len(profit_entries)} 筆利潤相關記錄")
    
    # 從最終利潤開始，逆向計算每筆記錄的餘額
    current_balance = correct_profit
    
    for entry in reversed(profit_entries):
        # 根據記錄類型調整餘額
        if entry.entry_type == "PROFIT_WITHDRAW" or "利潤提款" in entry.description:
            # 提款記錄：變動前餘額 = 當前餘額 + 提款金額
            entry.profit_before = current_balance + abs(entry.amount)
            entry.profit_after = current_balance
            entry.profit_change = -abs(entry.amount)
            current_balance = entry.profit_before
        elif entry.entry_type == "PROFIT_EARNED" or "售出利潤" in entry.description:
            # 利潤入庫：變動前餘額 = 當前餘額 - 利潤金額
            entry.profit_before = current_balance - entry.amount
            entry.profit_after = current_balance
            entry.profit_change = entry.amount
            current_balance = entry.profit_before
        else:
            # 其他情況：保持當前餘額
            entry.profit_before = current_balance
            entry.profit_after = current_balance
            entry.profit_change = 0
        
        print(f"記錄 {entry.id}: {entry.description} - 變動前: {entry.profit_before:.2f}, 變動後: {entry.profit_after:.2f}, 變動: {entry.profit_change:.2f}")
    
    # 提交修改
    db.session.commit()
    print("✅ LedgerEntry利潤餘額記錄修復完成")

def fix_cash_accounts_profit_balance(correct_profit):
    """修復CashAccount中的利潤餘額"""
    print("\n🔧 開始修復CashAccount中的利潤餘額...")
    
    # 找到主要的利潤帳戶（通常是TWD帳戶）
    twd_accounts = db.session.execute(
        db.select(CashAccount)
        .filter(CashAccount.currency == "TWD")
    ).scalars().all()
    
    if twd_accounts:
        # 將所有利潤分配到第一個TWD帳戶
        main_account = twd_accounts[0]
        main_account.profit_balance = correct_profit
        print(f"設定主要帳戶 {main_account.name} 的利潤餘額為: {correct_profit:.2f}")
        
        # 其他TWD帳戶的利潤餘額設為0
        for account in twd_accounts[1:]:
            account.profit_balance = 0.0
            print(f"設定帳戶 {account.name} 的利潤餘額為: 0.0")
        
        db.session.commit()
        print("✅ CashAccount利潤餘額修復完成")
    else:
        print("⚠️ 未找到TWD帳戶，跳過CashAccount修復")

def main():
    """主修復流程"""
    print("🚀 開始利潤計算修復流程...")
    
    with app.app_context():
        try:
            # 1. 計算正確的總利潤
            profit_data = calculate_correct_total_profit()
            correct_profit = profit_data['final_profit']
            
            print(f"\n📋 修復摘要:")
            print(f"   總銷售利潤: {profit_data['total_profit_from_sales']:.2f}")
            print(f"   總利潤提款: {profit_data['total_withdrawals']:.2f}")
            print(f"   最終利潤: {correct_profit:.2f}")
            
            # 2. 修復LedgerEntry中的利潤餘額記錄
            fix_ledger_entries_profit_balance(correct_profit)
            
            # 3. 修復CashAccount中的利潤餘額
            fix_cash_accounts_profit_balance(correct_profit)
            
            print(f"\n✅ 利潤計算修復完成！")
            print(f"   正確的利潤總額應該是: {correct_profit:.2f}")
            print(f"   請重新載入頁面查看修復結果")
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()
