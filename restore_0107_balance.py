#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回滾腳本：還原 0107 支付寶餘額

如果清理操作後發現 0107 餘額不對，可以使用此腳本還原
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import app, db, CashAccount

def restore_0107_balance():
    """還原 0107 支付寶餘額為 145,262.02 RMB"""
    print("=" * 80)
    print("回滾 0107 支付寶餘額")
    print("=" * 80)
    
    with app.app_context():
        try:
            # 查找 0107 支付寶帳戶
            account_0107 = db.session.execute(
                db.select(CashAccount)
                .filter(CashAccount.id == 27)  # 0107 支付寶的 ID
            ).scalar_one_or_none()
            
            if not account_0107:
                print("❌ 找不到 0107 支付寶帳戶 (ID: 27)")
                return 1
            
            print(f"\n找到帳戶: {account_0107.name} (ID: {account_0107.id})")
            print(f"當前餘額: {account_0107.balance:,.2f} RMB")
            
            # 原始餘額（清理前的值）
            original_balance = 145262.02
            current_balance = account_0107.balance
            
            if abs(current_balance - original_balance) < 0.01:
                print(f"\n✅ 餘額已經是原始值 ({original_balance:,.2f} RMB)，無需還原")
                return 0
            
            print(f"\n原始餘額（清理前）: {original_balance:,.2f} RMB")
            print(f"當前餘額: {current_balance:,.2f} RMB")
            print(f"差異: {current_balance - original_balance:,.2f} RMB")
            
            # 確認
            print("\n" + "=" * 80)
            response = input("是否還原為 145,262.02 RMB？(yes/no): ")
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return 0
            
            # 還原餘額
            account_0107.balance = original_balance
            db.session.commit()
            
            print(f"\n✅ 回滾完成！")
            print(f"   0107 支付寶餘額已還原為: {account_0107.balance:,.2f} RMB")
            print(f"\n⚠️  注意：WITHDRAW 記錄無法還原，只能還原餘額")
            
            return 0
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 回滾失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    print("回滾 0107 支付寶餘額工具")
    print("注意：此腳本只能還原餘額，無法還原已刪除的 WITHDRAW 記錄\n")
    
    exit_code = restore_0107_balance()
    sys.exit(exit_code)

