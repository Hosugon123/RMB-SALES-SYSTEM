#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理歷史售出扣款的 WITHDRAW LedgerEntry 記錄

問題說明：
- 過去的售出流程會創建 WITHDRAW LedgerEntry 記錄（"售出扣款"描述）
- 這些記錄現在是多餘的，因為售出記錄已經在流水頁面顯示了完整的扣款信息
- 這些重複的 WITHDRAW 記錄會造成流水頁面顯示混亂

修復策略：
1. 找到所有描述包含"售出扣款"的 WITHDRAW LedgerEntry
2. 回補錯誤扣款的帳戶餘額
3. 刪除這些重複的 LedgerEntry 記錄
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, LedgerEntry, CashAccount

def analyze_withdraw_records():
    """分析所有售出扣款的 WITHDRAW 記錄"""
    print("=" * 80)
    print("分析歷史售出扣款 WITHDRAW 記錄")
    print("=" * 80)
    
    # 查詢所有售出扣款的 WITHDRAW 記錄
    withdraw_records = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "WITHDRAW")
        .filter(LedgerEntry.description.like("%售出扣款%"))
    ).scalars().all()
    
    print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄\n")
    
    if len(withdraw_records) == 0:
        print("✅ 沒有找到需要清理的記錄！")
        return None
    
    # 按帳戶分組統計
    account_stats = {}
    total_amount = 0
    
    for record in withdraw_records:
        account_id = record.account_id
        if account_id not in account_stats:
            account_stats[account_id] = {
                'count': 0,
                'total_amount': 0,
                'account': record.account,
                'records': []
            }
        
        account_stats[account_id]['count'] += 1
        account_stats[account_id]['total_amount'] += abs(record.amount)
        account_stats[account_id]['records'].append(record)
        total_amount += abs(record.amount)
    
    print("統計資訊：")
    print("-" * 80)
    for account_id, stats in account_stats.items():
        account_name = stats['account'].name if stats['account'] else "未知帳戶"
        print(f"帳戶: {account_name} (ID: {account_id})")
        print(f"  記錄數量: {stats['count']} 筆")
        print(f"  總扣款金額: {stats['total_amount']:.2f} RMB")
    
    print("-" * 80)
    print(f"總記錄數: {len(withdraw_records)} 筆")
    print(f"總扣款金額: {total_amount:.2f} RMB")
    print()
    
    # 顯示前5筆記錄作為示例
    print("前5筆記錄示例：")
    print("-" * 80)
    for i, record in enumerate(withdraw_records[:5], 1):
        account_name = record.account.name if record.account else "未知帳戶"
        print(f"{i}. ID: {record.id}, 日期: {record.entry_date}, 帳戶: {account_name}")
        print(f"   金額: {record.amount:.2f} RMB, 描述: {record.description}")
    
    if len(withdraw_records) > 5:
        print(f"... 還有 {len(withdraw_records) - 5} 筆記錄")
    
    return {
        'records': withdraw_records,
        'account_stats': account_stats,
        'total_amount': total_amount
    }


def fix_withdraw_records(data, dry_run=True):
    """清理售出扣款的 WITHDRAW 記錄"""
    withdraw_records = data['records']
    account_stats = data['account_stats']
    
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN 模式：顯示清理計劃，不實際執行")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("執行實際清理")
        print("=" * 80)
    
    try:
        # 1. 回補所有帳戶的餘額
        for account_id, stats in account_stats.items():
            account = stats['account']
            if not account:
                print(f"⚠️  帳戶 ID {account_id} 不存在，跳過")
                continue
            
            old_balance = account.balance
            # 回補被錯誤扣除的金額
            account.balance += stats['total_amount']
            new_balance = account.balance
            
            if dry_run:
                print(f"\n[DRY RUN] 帳戶: {account.name}")
                print(f"  將回補: {stats['total_amount']:.2f} RMB")
                print(f"  餘額變化: {old_balance:.2f} -> {new_balance:.2f}")
            else:
                print(f"\n帳戶: {account.name}")
                print(f"  回補: {stats['total_amount']:.2f} RMB")
                print(f"  餘額變化: {old_balance:.2f} -> {new_balance:.2f}")
        
        # 2. 刪除所有 WITHDRAW 記錄
        if dry_run:
            print(f"\n[DRY RUN] 將刪除 {len(withdraw_records)} 筆 WITHDRAW LedgerEntry 記錄")
        else:
            print(f"\n刪除 {len(withdraw_records)} 筆 WITHDRAW LedgerEntry 記錄...")
            for record in withdraw_records:
                db.session.delete(record)
            print("✅ 記錄已刪除")
        
        if not dry_run:
            db.session.flush()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 清理失敗: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            db.session.rollback()
        return False


def main():
    """主程序"""
    import argparse
    
    print("=" * 80)
    print("清理歷史售出扣款 WITHDRAW 記錄腳本")
    print("=" * 80)
    
    parser = argparse.ArgumentParser(description='清理歷史售出扣款 WITHDRAW LedgerEntry 記錄')
    parser.add_argument('--dry-run', action='store_true', help='僅分析，不實際清理')
    parser.add_argument('--fix', action='store_true', help='執行實際清理')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("請指定 --dry-run（僅分析）或 --fix（執行清理）")
        return
    
    print(f"\n模式: {'DRY RUN（僅分析）' if args.dry_run else '實際清理'}")
    print("正在初始化應用程式...\n")
    
    with app.app_context():
        try:
            # 分析歷史數據
            data = analyze_withdraw_records()
            
            if data is None:
                return
            
            if args.dry_run:
                # 顯示清理計劃
                fix_withdraw_records(data, dry_run=True)
            elif args.fix:
                # 執行清理
                print("\n⚠️  警告：此操作會刪除 LedgerEntry 記錄並調整帳戶餘額！")
                print("⚠️  建議先執行 --dry-run 查看清理計劃")
                response = input("\n是否繼續？(yes/no): ")
                
                if response.lower() != 'yes':
                    print("❌ 操作已取消")
                    return
                
                if fix_withdraw_records(data, dry_run=False):
                    db.session.commit()
                    print("\n✅ 清理完成！")
                    print(f"   刪除記錄: {len(data['records'])} 筆")
                    print(f"   回補餘額: {data['total_amount']:.2f} RMB")
                else:
                    db.session.rollback()
                    print("\n❌ 清理失敗，已回滾")
        
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 腳本執行時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return


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

