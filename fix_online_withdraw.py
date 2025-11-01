#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清理線上資料庫中的售出扣款 WITHDRAW 記錄"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, LedgerEntry, CashAccount

def main():
    with app.app_context():
        try:
            # 查詢所有售出扣款的 WITHDRAW 記錄
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
            ).scalars().all()
            
            print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄\n")
            
            if len(withdraw_records) == 0:
                print("沒有需要清理的記錄！")
                return
            
            # 按帳戶統計
            account_stats = {}
            total_amount = 0
            
            for record in withdraw_records:
                account_id = record.account_id
                if account_id not in account_stats:
                    account_stats[account_id] = {
                        'count': 0,
                        'total_amount': 0,
                        'account': record.account
                    }
                account_stats[account_id]['count'] += 1
                account_stats[account_id]['total_amount'] += abs(record.amount)
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
            
            print("\n警告：此操作會刪除 LedgerEntry 記錄並調整帳戶餘額！")
            
            # 回補帳戶餘額
            for account_id, stats in account_stats.items():
                account = stats['account']
                if account:
                    old_balance = account.balance
                    account.balance += stats['total_amount']
                    new_balance = account.balance
                    print(f"\n帳戶 {account.name}: 回補 {stats['total_amount']:.2f} RMB")
                    print(f"  餘額變化: {old_balance:.2f} -> {new_balance:.2f}")
            
            # 刪除所有 WITHDRAW 記錄
            for record in withdraw_records:
                db.session.delete(record)
            
            db.session.commit()
            print(f"\n清理完成！")
            print(f"  刪除記錄: {len(withdraw_records)} 筆")
            print(f"  回補餘額: {total_amount:.2f} RMB")
            
        except Exception as e:
            db.session.rollback()
            print(f"清理失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"腳本執行失敗: {e}")
        import traceback
        traceback.print_exc()

