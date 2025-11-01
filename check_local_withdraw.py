#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查本地資料庫中的售出扣款 WITHDRAW 記錄"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 臨時移除環境變數中的 DATABASE_URL，強制使用本地資料庫
env_backup = None
if 'DATABASE_URL' in os.environ:
    env_backup = os.environ['DATABASE_URL']
    del os.environ['DATABASE_URL']

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
            
            # 顯示前10筆記錄
            print("前10筆記錄：")
            print("-" * 80)
            for i, record in enumerate(withdraw_records[:10], 1):
                account_name = record.account.name if record.account else "未知帳戶"
                print(f"{i}. ID: {record.id}, 日期: {record.entry_date}")
                print(f"   帳戶: {account_name}")
                print(f"   金額: {record.amount:.2f} RMB")
                print(f"   描述: {record.description}")
                print()
            
            if len(withdraw_records) > 10:
                print(f"... 還有 {len(withdraw_records) - 10} 筆記錄")
            
        except Exception as e:
            print(f"查詢失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"腳本執行失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢復環境變數
        if env_backup:
            os.environ['DATABASE_URL'] = env_backup

