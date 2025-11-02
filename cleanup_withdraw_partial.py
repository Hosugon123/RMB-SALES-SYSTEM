#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部分清理 WITHDRAW 記錄：只回補"從其他帳戶售出但使用該帳戶庫存"的錯誤扣款
針對 0107 支付寶：只回補 37,633.00 RMB（而不是完整的 WITHDRAW 總額）
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import app, db, LedgerEntry, CashAccount, SalesRecord, FIFOSalesAllocation, FIFOInventory

def cleanup_withdraw_partial():
    """部分清理：只回補錯誤的 WITHDRAW 扣款（WITHDRAW總額 - 銷售總額的差異）"""
    print("=" * 80)
    print("部分清理 WITHDRAW 記錄：只回補錯誤扣款")
    print("=" * 80)
    
    with app.app_context():
        try:
            # 查找 0107 支付寶帳戶
            account_0107 = db.session.execute(
                db.select(CashAccount)
                .filter(CashAccount.currency == "RMB")
                .filter(CashAccount.name.like("%0107%支付寶%"))
            ).scalar_one_or_none()
            
            if not account_0107:
                print("❌ 找不到 0107 支付寶帳戶")
                return 1
            
            print(f"\n找到帳戶: {account_0107.name} (ID: {account_0107.id})")
            print(f"當前餘額: {account_0107.balance:,.2f} RMB")
            
            # 計算 WITHDRAW 總額
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
                .filter(LedgerEntry.account_id == account_0107.id)
            ).scalars().all()
            
            withdraw_total = sum(abs(r.amount) for r in withdraw_records)
            print(f"  WITHDRAW 總額: {withdraw_total:,.2f} RMB ({len(withdraw_records)} 筆)")
            
            # 計算從 0107 售出的總額
            sales_from_0107 = db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.rmb_account_id == account_0107.id)
            ).scalars().all()
            
            sales_total = sum(s.rmb_amount for s in sales_from_0107)
            print(f"  從 0107 售出的總額: {sales_total:,.2f} RMB ({len(sales_from_0107)} 筆)")
            
            # 計算錯誤扣款（差異）
            error_amount = withdraw_total - sales_total
            print(f"  錯誤扣款（差異）: {error_amount:,.2f} RMB")
            
            if error_amount <= 0:
                print("✅ 沒有發現錯誤扣款，WITHDRAW 總額小於或等於銷售總額")
                print("   建議執行完整清理: flask cleanup-sales-withdraw")
                return 0
            
            # 顯示將要執行的操作
            print(f"\n將要執行的操作：")
            print(f"  1. 回補 0107 支付寶餘額: {error_amount:,.2f} RMB（只回補差異部分）")
            print(f"  2. 刪除所有售出扣款 WITHDRAW 記錄: {len(withdraw_records)} 筆")
            print(f"  3. 清理後餘額: {account_0107.balance + error_amount:,.2f} RMB")
            print(f"     （預期餘額：145,262.02 + 37,633.00 = 182,895.02 RMB）")
            
            # 確認
            response = input("\n是否繼續？(yes/no): ")
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return 0
            
            # 回補餘額（只回補差異部分）
            old_balance = account_0107.balance
            account_0107.balance += error_amount
            new_balance = account_0107.balance
            
            print(f"\n✅ 回補 0107 支付寶餘額: {error_amount:,.2f} RMB")
            print(f"   餘額變化: {old_balance:,.2f} -> {new_balance:,.2f}")
            
            # 刪除所有 WITHDRAW 記錄
            deleted_count = 0
            for record in withdraw_records:
                db.session.delete(record)
                deleted_count += 1
            
            db.session.commit()
            
            print(f"\n✅ 清理完成！")
            print(f"   刪除 WITHDRAW 記錄: {deleted_count} 筆")
            print(f"   回補餘額: {error_amount:,.2f} RMB")
            print(f"   新餘額: {new_balance:,.2f} RMB")
            
            # 驗證
            if abs(new_balance - 182895.02) < 1.0:
                print(f"   ✅ 餘額與預期一致（182,895.02 RMB）")
            else:
                print(f"   ⚠️  餘額與預期略有差異（預期 182,895.02 RMB）")
            
            return 0
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清理失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    print("部分清理 WITHDRAW 記錄工具")
    print("只回補從其他帳戶售出但使用該帳戶庫存的錯誤扣款\n")
    
    exit_code = cleanup_withdraw_partial()
    sys.exit(exit_code)

