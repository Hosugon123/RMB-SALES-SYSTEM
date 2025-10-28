#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歷史 SalesRecord 的 LedgerEntry 修正腳本
修正缺失的 LedgerEntry 記錄， emphasize RMB 帳戶餘額變動有正確記錄
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_and_fix_historical_sales():
    """檢查並修正歷史銷售記錄的 LedgerEntry"""
    # 在函數內部導入，確保 app.py 已完全載入
    from app import app, db, SalesRecord, LedgerEntry, FIFOSalesAllocation, CashAccount, FIFOInventory
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    print("=" * 80)
    print("開始檢查歷史 SalesRecord 的 LedgerEntry 記錄...")
    print("=" * 80)
    
    with app.app_context():
        # 1. 獲取所有銷售記錄
        all_sales = db.session.execute(
            select(SalesRecord).order_by(SalesRecord.created_at.asc())
        ).scalars().all()
        
        print(f"\n📊 共有 {len(all_sales)} 筆銷售記錄需要檢查\n")
        
        missing_entries = []
        
        for sale in all_sales:
            # 3. 獲取該銷售記錄的 FIFO 分配
            allocations = db.session.execute(
                select(FIFOSalesAllocation)
                .filter_by(sales_record_id=sale.id)
            ).scalars().all()
            
            if not allocations:
                print(f"⚠️  銷售記錄 ID {sale.id}: 沒有 FIFO 分配記錄")
                continue
            
            # 4. 檢查是否缺少 LedgerEntry
            expected_accounts = set()
            for allocation in allocations:
                inventory = allocation.fifo_inventory
                if inventory and inventory.purchase_record and inventory.purchase_record.deposit_account:
                    expected_accounts.add((inventory.purchase_record.deposit_account.id, allocation.allocated_rmb))
            
            if not expected_accounts:
                print(f"⚠️  銷售記錄 ID {sale.id}: 無法確定扣款帳戶")
                continue
            
            # 檢查是否有對應的 LedgerEntry
            found_entries = []
            for account_id, amount in expected_accounts:
                # 查找相關的 LedgerEntry（在銷售記錄時間的前後5分鐘內）
                entry = db.session.execute(
                    select(LedgerEntry)
                    .filter_by(
                        entry_type="WITHDRAW",
                        account_id=account_id
                    )
                    .filter(LedgerEntry.amount == -amount)  # 負數
                    .filter(LedgerEntry.entry_date >= sale.created_at - timedelta(minutes=5))
                    .filter(LedgerEntry.entry_date <= sale.created_at + timedelta(minutes=5))
                    .limit(1)
                ).scalar_one_or_none()
                
                if entry:
                    found_entries.append((entry, account_id, amount))
            
            # 如果沒有找到完整的記錄
            if len(found_entries) < len(expected_accounts):
                missing_entries.append({
                    'sale': sale,
                    'expected_accounts': expected_accounts,
                    'found_entries': found_entries,
                    'allocations': allocations
                })
                print(f"❌ 銷售記錄 ID {sale.id}: 缺少 LedgerEntry 記錄")
                print(f"   預期帳戶數: {len(expected_accounts)}, 找到: {len(found_entries)}")
        
        print("\n" + "=" * 80)
        print(f"發現 {len(missing_entries)} 筆銷售記錄缺少 LedgerEntry")
        print("=" * 80)
        
        if not missing_entries:
            print("\n✅ 所有銷售記錄都有正確的 LedgerEntry，無需修正！")
            return True
        
        # 5. 修正缺失的記錄
        print("\n開始修正缺失的 LedgerEntry 記錄...\n")
        
        for item in missing_entries:
            sale = item['sale']
            allocations = item['allocations']
            found_accounts = {entry[1] for entry in item['found_entries']}
            
            print(f"修正銷售記錄 ID {sale.id}...")
            
            for allocation in allocations:
                try:
                    inventory = allocation.fifo_inventory
                    if not inventory or not inventory.purchase_record or not inventory.purchase_record.deposit_account:
                        continue
                    
                    source_account = inventory.purchase_record.deposit_account
                    
                    # 如果已經有記錄，跳過
                    if source_account.id in found_accounts:
                        continue
                    
                    # 創建缺失的 LedgerEntry
                    ledger_entry = LedgerEntry(
                        entry_type="WITHDRAW",
                        account_id=source_account.id,
                        amount=-allocation.allocated_rmb,  # 負數表示出款
                        description=f"售出扣款：分配給客戶（庫存批次 {inventory.id}）[歷史修正]",
                        entry_date=sale.created_at,  # 使用原銷售記錄的時間
                        operator_id=1  # 假設為系統修正
                    )
                    db.session.add(ledger_entry)
                    print(f"  ✓ 已為帳戶 {source_account.name} 創建 LedgerEntry (-{allocation.allocated_rmb:.2f} RMB)")
                
                except Exception as e:
                    print(f"  ✗ 創建 LedgerEntry 失敗: {e}")
                    continue
        
        try:
            db.session.commit()
            print(f"\n✅ 成功修正 {len(missing_entries)} 筆銷售記錄的 LedgerEntry！")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 修正失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

def verify_account_balances():
    """驗證帳戶餘額是否正確"""
    # 在函數內部導入，確保 app.py 已完全載入
    from app import app, db, LedgerEntry, CashAccount
    from sqlalchemy import select
    
    print("\n" + "=" * 80)
    print("驗證帳戶餘額...")
    print("=" * 80)
    
    with app.app_context():
        # 重新計算所有帳戶的餘額
        all_accounts = db.session.execute(select(CashAccount)).scalars().all()
        
        print("\n📊 帳戶餘額驗證報告：\n")
        
        for account in all_accounts:
            # 計算 LedgerEntry 的總和
            ledgers = db.session.execute(
                select(LedgerEntry)
                .filter_by(account_id=account.id)
            ).scalars().all()
            
            calculated_balance = sum(entry.amount for entry in ledgers)
            actual_balance = account.balance
            
            if abs(calculated_balance - actual_balance) > 0.01:  # 允許小數誤差
                print(f"⚠️  帳戶 {account.name} ({account.currency}):")
                print(f"   實際餘額: {actual_balance:.2f}")
                print(f"   LedgerEntry 計算餘額: {calculated_balance:.2f}")
                print(f"   差異: {actual_balance - calculated_balance:.2f}")
            else:
                print(f"✅ 帳戶 {account.name} ({account.currency}): 餘額正確 ({actual_balance:.2f})")

if __name__ == "__main__":
    print("歷史 SalesRecord LedgerEntry 修正腳本")
    print("此腳本會修正歷史銷售記錄中缺失的 LedgerEntry")
    print("\n警告：此操作會修改資料庫記錄！")
    
    response = input("\n是否繼續？(yes/no): ")
    if response.lower() != "yes":
        print("已取消")
        sys.exit(0)
    
    # 執行修正
    success = check_and_fix_historical_sales()
    
    if success:
        # 驗證餘額
        verify_account_balances()
        
        print("\n" + "=" * 80)
        print("✅ 修正完成！")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 修正失敗！請檢查錯誤訊息")
        print("=" * 80)

