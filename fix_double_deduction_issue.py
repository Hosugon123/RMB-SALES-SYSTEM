#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復雙重扣款問題
結合兩個問題：
1. 從錯誤帳戶扣款
2. 重複的 WITHDRAW LedgerEntry

問題說明：
舊代碼的流程：
1. 從售出的扣款戶扣款（正確）
2. 創建 WITHDRAW LedgerEntry（但可能從錯誤帳戶扣款或重複）

修復策略：
1. 識別所有錯誤的 WITHDRAW 記錄
2. 回補錯誤扣款的帳戶
3. 刪除所有重複的 WITHDRAW 記錄
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, SalesRecord, FIFOSalesAllocation, CashAccount, LedgerEntry
from sqlalchemy import func

def analyze_double_deduction_issues():
    """分析雙重扣款問題"""
    print("=" * 100)
    print("分析歷史售出扣款問題")
    print("=" * 100)
    
    # 1. 查找所有售出扣款 WITHDRAW 記錄
    withdraw_records = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "WITHDRAW")
        .filter(LedgerEntry.description.like("%售出扣款%"))
    ).scalars().all()
    
    print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
    
    if len(withdraw_records) == 0:
        print("✅ 沒有需要清理的記錄！")
        return None, None
    
    # 2. 分析這些記錄
    account_stats = {}
    issues_by_sale = {}
    
    for record in withdraw_records:
        account_id = record.account_id
        
        # 按帳戶統計
        if account_id not in account_stats:
            account_stats[account_id] = {
                'count': 0,
                'total_amount': 0,
                'account': record.account,
                'records': []
            }
        
        account_stats[account_id]['count'] += 1
        abs_amount = abs(record.amount)
        account_stats[account_id]['total_amount'] += abs_amount
        account_stats[account_id]['records'].append(record)
        
        # 嘗試從描述中提取銷售記錄ID
        import re
        match = re.search(r'銷售記錄 ID (\d+)', record.description)
        if match:
            sale_id = int(match.group(1))
            if sale_id not in issues_by_sale:
                issues_by_sale[sale_id] = {
                    'sale': None,
                    'withdraw_records': []
                }
            issues_by_sale[sale_id]['withdraw_records'].append(record)
    
    # 3. 獲取銷售記錄信息
    for sale_id in issues_by_sale:
        sale = db.session.get(SalesRecord, sale_id)
        issues_by_sale[sale_id]['sale'] = sale
    
    # 4. 打印統計
    print("\n按帳戶統計：")
    print("-" * 100)
    total_amount = 0
    for account_id, stats in account_stats.items():
        account_name = stats['account'].name if stats['account'] else "未知帳戶"
        print(f"\n帳戶: {account_name} (ID: {account_id})")
        print(f"  記錄數量: {stats['count']} 筆")
        print(f"  總金額: {stats['total_amount']:.2f} RMB")
        total_amount += stats['total_amount']
    
    print("-" * 100)
    print(f"總記錄數: {len(withdraw_records)} 筆")
    print(f"總金額: {total_amount:.2f} RMB")
    
    # 5. 分析每個銷售記錄
    print("\n按銷售記錄分析：")
    print("-" * 100)
    
    wrong_account_issues = []
    
    for sale_id, issue in issues_by_sale.items():
        sale = issue['sale']
        if not sale:
            continue
            
        records = issue['withdraw_records']
        
        print(f"\n銷售記錄 ID {sale_id}:")
        if sale:
            print(f"  客戶: {sale.customer.name if sale.customer else 'N/A'}")
            print(f"  金額: {sale.rmb_amount:.2f} RMB")
            print(f"  扣款戶: {sale.rmb_account.name if sale.rmb_account else 'N/A'} (ID: {sale.rmb_account_id})")
        else:
            print(f"  ⚠️  找不到銷售記錄")
        
        print(f"  對應的 WITHDRAW 記錄: {len(records)} 筆")
        
        for record in records:
            account_name = record.account.name if record.account else "未知"
            print(f"    - 帳戶: {account_name} (ID: {record.account_id}), 金額: {abs(record.amount):.2f} RMB")
            
            # 檢查是否從正確帳戶扣款
            if sale and record.account_id != sale.rmb_account_id:
                print(f"      ⚠️  錯誤：從錯誤帳戶扣款！")
                wrong_account_issues.append({
                    'sale': sale,
                    'record': record,
                    'correct_account': sale.rmb_account,
                    'wrong_account': record.account
                })
    
    return account_stats, wrong_account_issues


def fix_double_deduction(account_stats, wrong_account_issues, dry_run=True):
    """修復雙重扣款問題"""
    
    if dry_run:
        print("\n" + "=" * 100)
        print("DRY RUN 模式：僅顯示修復方案")
        print("=" * 100)
    else:
        print("\n" + "=" * 100)
        print("開始修復雙重扣款問題")
        print("=" * 100)
    
    try:
        # 1. 處理從錯誤帳戶扣款的問題
        if wrong_account_issues:
            print("\n【步驟1】修復從錯誤帳戶扣款的問題")
            print("-" * 100)
            
            # 統計每個帳戶需要調整的金額
            adjustment_needed = {}
            
            for issue in wrong_account_issues:
                record = issue['record']
                correct_account = issue['correct_account']
                wrong_account = issue['wrong_account']
                
                # 錯誤帳戶需要回補
                if wrong_account.id not in adjustment_needed:
                    adjustment_needed[wrong_account.id] = 0
                adjustment_needed[wrong_account.id] += abs(record.amount)
                
                # 正確帳戶需要扣款
                if correct_account.id not in adjustment_needed:
                    adjustment_needed[correct_account.id] = 0
                adjustment_needed[correct_account.id] -= abs(record.amount)
                
                print(f"\n銷售記錄 ID {issue['sale'].id}:")
                print(f"  錯誤扣款: {wrong_account.name} (ID: {wrong_account.id})")
                print(f"  正確扣款: {correct_account.name} (ID: {correct_account.id})")
                print(f"  金額: {abs(record.amount):.2f} RMB")
                
                if not dry_run:
                    print(f"  ✅ 已記錄到調整清單")
        
        # 2. 處理所有 WITHDRAW 記錄的刪除和回補
        print("\n【步驟2】處理所有售出扣款 WITHDRAW 記錄")
        print("-" * 100)
        
        total_deleted = 0
        
        for account_id, stats in account_stats.items():
            account = stats['account']
            if account:
                old_balance = account.balance
                
                # 計算調整金額
                # 如果這個帳戶在調整清單中，考慮調整
                adjustment = adjustment_needed.get(account_id, 0)
                final_adjustment = stats['total_amount'] + adjustment
                
                if final_adjustment != 0:
                    new_balance = account.balance + final_adjustment
                    
                    print(f"\n帳戶: {account.name} (ID: {account_id})")
                    print(f"  當前餘額: {old_balance:.2f} RMB")
                    print(f"  WITHDRAW 記錄總額: {stats['total_amount']:.2f} RMB")
                    if adjustment != 0:
                        print(f"  錯誤帳戶調整: {adjustment:+.2f} RMB")
                    print(f"  總調整: {final_adjustment:+.2f} RMB")
                    print(f"  調整後餘額: {new_balance:.2f} RMB")
                    
                    if not dry_run:
                        account.balance = new_balance
                        print(f"  ✅ 已更新餘額")
                
                total_deleted += stats['count']
        
        # 3. 刪除所有 WITHDRAW 記錄
        if not dry_run:
            print("\n【步驟3】刪除所有售出扣款 WITHDRAW 記錄")
            print("-" * 100)
            
            for account_id, stats in account_stats.items():
                for record in stats['records']:
                    db.session.delete(record)
            
            print(f"✅ 已標記 {total_deleted} 筆記錄待刪除")
        
        # 提交所有變更
        if not dry_run:
            db.session.commit()
            print(f"\n✅ 修復完成！")
            print(f"   刪除記錄: {total_deleted} 筆")
            print(f"   調整帳戶: {len([a for a in account_stats.values() if adjustment_needed.get(a['account'].id, 0) != 0])} 個")
        else:
            print(f"\n✅ DRY RUN 完成")
            print(f"   將刪除記錄: {total_deleted} 筆")
            print(f"   將調整帳戶: {len([a for a in account_stats.values() if adjustment_needed.get(a['account'].id, 0) != 0])} 個")
    
    except Exception as e:
        if not dry_run:
            db.session.rollback()
        print(f"\n❌ 修復失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def main():
    """主程序"""
    with app.app_context():
        try:
            # 分析問題
            account_stats, wrong_account_issues = analyze_double_deduction_issues()
            
            if account_stats is None:
                return 0
            
            # 確認是否執行
            print("\n" + "=" * 100)
            print("是否執行修復？")
            print("=" * 100)
            print("\n⚠️  警告：此操作會修改帳戶餘額並刪除 LedgerEntry 記錄！")
            print("\n請選擇：")
            print("1. 執行 DRY RUN（僅分析，不實際修改）")
            print("2. 執行實際修復（需要確認）")
            print("3. 取消")
            
            response = input("\n請輸入選項 (1/2/3): ").strip()
            
            if response == '1':
                # DRY RUN
                fix_double_deduction(account_stats, wrong_account_issues, dry_run=True)
            elif response == '2':
                # 實際修復
                confirm = input("\n⚠️  確認要執行實際修復嗎？(yes/no): ").strip()
                if confirm.lower() == 'yes':
                    fix_double_deduction(account_stats, wrong_account_issues, dry_run=False)
                else:
                    print("❌ 操作已取消")
            else:
                print("❌ 操作已取消")
            
        except Exception as e:
            print(f"\n❌ 程序執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0


if __name__ == '__main__':
    main()

