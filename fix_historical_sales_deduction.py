#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復歷史售出扣款邏輯錯誤

問題說明：
- 過去的扣款邏輯從庫存來源帳戶（inventory.purchase_record.deposit_account）扣款
- 正確的邏輯應該從售出的扣款戶（sales_record.rmb_account）扣款

修復策略：
1. 找到所有有FIFO分配的銷售記錄
2. 檢查每條記錄的扣款帳戶是否正確
3. 修正錯誤的扣款：
   - 回補錯誤扣款的帳戶（庫存來源帳戶）
   - 從正確的帳戶扣款（銷售記錄的扣款戶）
   - 修正相關的LedgerEntry記錄
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app import app, db
from sqlalchemy import text
# 嘗試從models導入，如果失敗則從app導入
try:
    from models import SalesRecord, FIFOSalesAllocation, CashAccount, LedgerEntry, Customer
except ImportError:
    from app import SalesRecord, FIFOSalesAllocation, CashAccount, LedgerEntry, Customer

try:
    from app import FIFOInventory, PurchaseRecord
except ImportError:
    # 在app_context中動態獲取
    FIFOInventory = None
    PurchaseRecord = None


def analyze_historical_sales():
    """分析歷史銷售記錄，找出需要修正的記錄"""
    print("=" * 80)
    print("分析歷史銷售記錄扣款邏輯")
    print("=" * 80)
    
    # 測試資料庫連接
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ 資料庫連接成功")
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        print("\n建議解決方案：")
        print("1. 檢查網絡連接")
        print("2. 確認資料庫服務器是否在線")
        print("3. 檢查 DATABASE_URL 環境變數是否正確")
        print("4. 如果是 SSL 連接問題，可能需要重新連接")
        print("5. 等待幾分鐘後再試（可能是暫時的網絡問題）")
        raise
    
    # 獲取所有有FIFO分配的銷售記錄
    # 使用子查詢來找到有分配的銷售記錄
    sales_with_allocations = []
    try:
        all_allocations = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
        sales_ids_with_allocations = set(alloc.sales_record_id for alloc in all_allocations)
        
        for sale_id in sales_ids_with_allocations:
            sale = db.session.get(SalesRecord, sale_id)
            if sale:
                sales_with_allocations.append(sale)
    except Exception as e:
        print(f"❌ 查詢資料庫時發生錯誤: {e}")
        print("嘗試重新連接資料庫...")
        db.session.rollback()
        try:
            db.session.execute(text("SELECT 1"))
            print("✅ 重新連接成功，請重新運行腳本")
        except Exception as reconnect_error:
            print(f"❌ 重新連接失敗: {reconnect_error}")
        raise
    
    print(f"\n找到 {len(sales_with_allocations)} 筆有FIFO分配的銷售記錄\n")
    
    issues = []  # 需要修正的記錄
    
    for sale in sales_with_allocations:
        if not sale.rmb_account:
            print(f"⚠️  銷售記錄 ID {sale.id} 沒有指定扣款戶，跳過")
            continue
        
        # 獲取該銷售記錄的所有FIFO分配
        allocations = (
            db.session.execute(
                db.select(FIFOSalesAllocation)
                .filter(FIFOSalesAllocation.sales_record_id == sale.id)
            )
            .scalars()
            .all()
        )
        
        # 檢查是否有從錯誤帳戶扣款的記錄
        # 錯誤：從庫存來源帳戶扣款的LedgerEntry
        # 正確：應該從sales_record.rmb_account扣款
        
        # 查找與此銷售記錄相關的所有 WITHDRAW LedgerEntry（描述包含"售出扣款"和銷售記錄ID）
        all_sale_ledger_entries = (
            db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like(f"%售出扣款%"))
                .filter(LedgerEntry.description.like(f"%銷售記錄 ID {sale.id}%"))
            )
            .scalars()
            .all()
        )
        
        # 分類：錯誤的記錄（從錯誤帳戶扣款，或 amount 為正數）
        wrong_ledger_entries = []
        # 正確的記錄（從正確帳戶扣款，且 amount 為負數）
        correct_ledger_entries = []
        
        for entry in all_sale_ledger_entries:
            # 檢查是否為錯誤記錄：
            # 1. 從錯誤帳戶扣款（不是 sales_record.rmb_account）
            # 2. amount 為正數（應該為負數，表示扣款）
            if entry.account_id != sale.rmb_account_id or entry.amount > 0:
                wrong_ledger_entries.append(entry)
            else:
                # 從正確帳戶扣款且 amount 為負數
                correct_ledger_entries.append(entry)
        
        # 也檢查是否有從錯誤帳戶扣款的記錄（舊邏輯從庫存來源帳戶扣款）
        wrong_account_entries = (
            db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(
                    (LedgerEntry.description.like(f"%售出扣款%")) |
                    (LedgerEntry.description.like(f"%庫存批次%"))
                )
                .filter(LedgerEntry.account_id != sale.rmb_account_id)
            )
            .scalars()
            .all()
        )
        
        # 將錯誤帳戶的記錄也加入 wrong_ledger_entries（避免重複）
        for entry in wrong_account_entries:
            if entry not in wrong_ledger_entries:
                wrong_ledger_entries.append(entry)
        
        # 如果沒有正確的扣款記錄，或者有錯誤的扣款記錄，則需要修正
        if len(wrong_ledger_entries) > 0 or len(correct_ledger_entries) == 0:
            total_wrong_deduction = sum(abs(entry.amount) for entry in wrong_ledger_entries)
            total_correct_deduction = sum(abs(entry.amount) for entry in correct_ledger_entries)
            
            issue = {
                'sale': sale,
                'allocations': allocations,
                'wrong_ledger_entries': wrong_ledger_entries,
                'correct_ledger_entries': correct_ledger_entries,
                'wrong_deduction_total': total_wrong_deduction,
                'correct_deduction_total': total_correct_deduction,
                'expected_deduction': sale.rmb_amount
            }
            issues.append(issue)
            
            print(f"❌ 銷售記錄 ID {sale.id}（客戶：{sale.customer.name if sale.customer else 'N/A'}）")
            print(f"   扣款戶：{sale.rmb_account.name if sale.rmb_account else 'N/A'}")
            print(f"   銷售金額：{sale.rmb_amount:.2f} RMB")
            print(f"   錯誤扣款記錄：{len(wrong_ledger_entries)} 筆，總計：{total_wrong_deduction:.2f} RMB")
            print(f"   正確扣款記錄：{len(correct_ledger_entries)} 筆，總計：{total_correct_deduction:.2f} RMB")
            print(f"   預期扣款：{sale.rmb_amount:.2f} RMB")
            print()
    
    return issues


def fix_sales_deduction(issue, dry_run=True):
    """修正單個銷售記錄的扣款錯誤"""
    sale = issue['sale']
    wrong_entries = issue['wrong_ledger_entries']
    correct_entries = issue['correct_ledger_entries']
    expected_deduction = issue['expected_deduction']
    
    if dry_run:
        print(f"[DRY RUN] 準備修正銷售記錄 ID {sale.id}")
    else:
        print(f"修正銷售記錄 ID {sale.id}")
    
    try:
        # 1. 回補錯誤扣款的帳戶或修正錯誤的增加
        wrong_accounts_to_adjust = {}
        
        for entry in wrong_entries:
            account_id = entry.account_id
            if account_id not in wrong_accounts_to_adjust:
                wrong_accounts_to_adjust[account_id] = 0
            
            # 如果 amount 為正數，說明錯誤地增加了餘額，需要扣除
            # 如果 amount 為負數，說明錯誤地扣除了餘額，需要回補
            if entry.amount > 0:
                # amount 為正數：錯誤地增加了餘額，需要扣除
                wrong_accounts_to_adjust[account_id] -= entry.amount
            else:
                # amount 為負數：錯誤地扣除了餘額，需要回補
                wrong_accounts_to_adjust[account_id] += abs(entry.amount)
        
        for account_id, adjustment_amount in wrong_accounts_to_adjust.items():
            account = db.session.get(CashAccount, account_id)
            if account:
                old_balance = account.balance
                account.balance += adjustment_amount  # adjustment_amount 可能為正（回補）或負（扣除）
                new_balance = account.balance
                
                adjustment_symbol = "+" if adjustment_amount >= 0 else ""
                if dry_run:
                    print(f"  [DRY RUN] 調整帳戶 {account.name}: {old_balance:.2f} -> {new_balance:.2f} ({adjustment_symbol}{adjustment_amount:.2f} RMB)")
                else:
                    print(f"  調整帳戶 {account.name}: {old_balance:.2f} -> {new_balance:.2f} ({adjustment_symbol}{adjustment_amount:.2f} RMB)")
        
        # 2. 計算扣款戶需要調整的餘額
        correct_account = sale.rmb_account
        if not correct_account:
            raise ValueError(f"銷售記錄 ID {sale.id} 沒有扣款戶")
        
        # 計算當前已正確扣款的金額（correct_entries 中 amount 為負數的總和）
        current_correct_deduction = sum(entry.amount for entry in correct_entries if entry.amount < 0)
        current_correct_deduction = abs(current_correct_deduction)  # 轉為正數
        
        # 如果扣款戶在錯誤記錄中（可能被錯誤地增加或減少），需要先調整
        if correct_account.id in wrong_accounts_to_adjust:
            # 扣款戶的餘額已經在步驟1中調整過了，這裡需要更新預期的扣款金額
            # 因為如果錯誤記錄是正數（錯誤增加），調整後餘額已經減少了，不需要再次扣款
            # 如果錯誤記錄是負數（錯誤扣款），調整後餘額已經回補了，需要正常扣款
            pass  # 餘額調整已在步驟1完成
        
        # 計算還需要扣款的金額
        deduction_needed = expected_deduction - current_correct_deduction
        
        if deduction_needed > 0:
            # 檢查餘額是否足夠
            if correct_account.balance < deduction_needed:
                raise ValueError(
                    f"扣款戶 {correct_account.name} 餘額不足！"
                    f"需要 {deduction_needed:.2f} RMB，但僅剩 {correct_account.balance:.2f} RMB"
                )
            
            old_balance = correct_account.balance
            correct_account.balance -= deduction_needed
            new_balance = correct_account.balance
            
            if dry_run:
                print(f"  [DRY RUN] 從扣款戶 {correct_account.name} 扣款: {old_balance:.2f} -> {new_balance:.2f} (-{deduction_needed:.2f} RMB)")
            else:
                print(f"  從扣款戶 {correct_account.name} 扣款: {old_balance:.2f} -> {new_balance:.2f} (-{deduction_needed:.2f} RMB)")
                
                # 創建正確的LedgerEntry
                ledger_entry = LedgerEntry(
                    entry_type="WITHDRAW",
                    account_id=correct_account.id,
                    amount=-deduction_needed,
                    description=f"售出扣款修正：客戶 {sale.customer.name if sale.customer else 'N/A'}，銷售記錄 ID {sale.id}",
                    operator_id=1  # 系統修復
                )
                db.session.add(ledger_entry)
                print(f"  創建正確的LedgerEntry記錄")
        
        # 3. 標記或刪除錯誤的LedgerEntry記錄
        for entry in wrong_entries:
            if dry_run:
                print(f"  [DRY RUN] 將刪除錯誤的LedgerEntry ID {entry.id}")
            else:
                # 可以選擇刪除或標記為已修正
                db.session.delete(entry)
                print(f"  刪除錯誤的LedgerEntry ID {entry.id}")
        
        if not dry_run:
            db.session.flush()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 修正失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程序"""
    import argparse
    
    print("=" * 80)
    print("歷史售出扣款邏輯修復腳本")
    print("=" * 80)
    
    parser = argparse.ArgumentParser(description='修復歷史售出扣款邏輯錯誤')
    parser.add_argument('--dry-run', action='store_true', help='僅分析，不實際修正')
    parser.add_argument('--fix', action='store_true', help='執行實際修正')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("請指定 --dry-run（僅分析）或 --fix（執行修正）")
        return
    
    print(f"\n模式: {'DRY RUN（僅分析）' if args.dry_run else '實際修正'}")
    print("正在初始化應用程式...\n")
    
    with app.app_context():
        # 添加重試機制
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 分析歷史數據
                issues = analyze_historical_sales()
                break  # 成功則跳出循環
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n⚠️  發生錯誤（嘗試 {retry_count}/{max_retries}）: {e}")
                    print("等待 5 秒後重試...")
                    import time
                    time.sleep(5)
                    # 清理 session
                    db.session.rollback()
                    try:
                        db.session.close()
                    except:
                        pass
                else:
                    print(f"\n❌ 重試 {max_retries} 次後仍然失敗")
                    print("\n可能的解決方案：")
                    print("1. 檢查網絡連接和資料庫服務器狀態")
                    print("2. 如果是遠程 PostgreSQL，檢查防火牆設置")
                    print("3. 嘗試使用本地資料庫備份運行修復腳本")
                    print("4. 聯繫資料庫管理員檢查服務器狀態")
                    raise
        
        if len(issues) == 0:
            print("\n✅ 沒有發現需要修正的記錄！")
            return
        
        print(f"\n發現 {len(issues)} 筆需要修正的銷售記錄\n")
        
        if args.dry_run:
            print("=" * 80)
            print("DRY RUN 模式：僅顯示修正計劃，不實際執行")
            print("=" * 80)
            
            for i, issue in enumerate(issues, 1):
                print(f"\n[{i}/{len(issues)}] 修正計劃：")
                fix_sales_deduction(issue, dry_run=True)
        elif args.fix:
            print("=" * 80)
            print("執行實際修正")
            print("=" * 80)
            print("\n⚠️  警告：此操作會修改資料庫！")
            print("⚠️  建議先執行 --dry-run 查看修正計劃")
            response = input("\n是否繼續？(yes/no): ")
            
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return
            
            success_count = 0
            fail_count = 0
            
            for i, issue in enumerate(issues, 1):
                print(f"\n[{i}/{len(issues)}] 正在修正：")
                if fix_sales_deduction(issue, dry_run=False):
                    success_count += 1
                else:
                    fail_count += 1
            
            if success_count > 0:
                try:
                    db.session.commit()
                    print(f"\n✅ 修正完成！成功：{success_count} 筆，失敗：{fail_count} 筆")
                except Exception as e:
                    db.session.rollback()
                    print(f"\n❌ 提交失敗: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                db.session.rollback()
                print("\n❌ 所有修正都失敗，已回滾")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 腳本執行時發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

