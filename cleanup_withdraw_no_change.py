#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 WITHDRAW 記錄，但保持帳戶餘額不變（除了 0107 需要調整錯誤扣款）

執行結果：
- 0107 支付寶：餘額調整為 182,895.02 RMB（加回 37,633.00）
- 7773 支付寶：餘額保持 58,423.83 RMB（不變）
- 6186 支付寶：餘額保持 1,067.00 RMB（不變）
- 所有售出扣款 WITHDRAW 記錄：刪除
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import app, db, LedgerEntry, CashAccount, SalesRecord

def cleanup_withdraw_no_change():
    """清理 WITHDRAW 記錄，0107 只調整錯誤部分，其他帳戶保持不變"""
    print("=" * 80)
    print("清理 WITHDRAW 記錄（保持帳戶餘額不變）")
    print("=" * 80)
    
    with app.app_context():
        try:
            # 查找所有售出扣款 WITHDRAW 記錄
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
            ).scalars().all()
            
            if len(withdraw_records) == 0:
                print("✅ 沒有找到需要清理的 WITHDRAW 記錄")
                return 0
            
            print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
            
            # 按帳戶統計
            account_stats = {}
            for record in withdraw_records:
                account_id = record.account_id
                if account_id not in account_stats:
                    account = record.account
                    account_stats[account_id] = {
                        'account': account,
                        'records': [],
                        'total_amount': 0
                    }
                account_stats[account_id]['records'].append(record)
                account_stats[account_id]['total_amount'] += abs(record.amount)
            
            print("\n各帳戶的 WITHDRAW 統計：")
            print("-" * 80)
            for account_id, stats in account_stats.items():
                account_name = stats['account'].name if stats['account'] else f"ID:{account_id}"
                print(f"  {account_name} (ID: {account_id}):")
                print(f"    當前餘額: {stats['account'].balance:,.2f} RMB" if stats['account'] else "    帳戶不存在")
                print(f"    WITHDRAW 總額: {stats['total_amount']:,.2f} RMB ({len(stats['records'])} 筆)")
            
            # 查找 0107 支付寶帳戶，計算需要調整的金額
            account_0107 = None
            adjustment_0107 = 0.0
            
            for account_id, stats in account_stats.items():
                account = stats['account']
                if account and '0107' in account.name and '支付寶' in account.name:
                    account_0107 = account
                    
                    # 計算從 0107 售出的總額
                    sales_from_0107 = db.session.execute(
                        db.select(SalesRecord)
                        .filter(SalesRecord.rmb_account_id == account_0107.id)
                    ).scalars().all()
                    
                    sales_total = sum(s.rmb_amount for s in sales_from_0107)
                    
                    # 錯誤扣款 = WITHDRAW 總額 - 銷售總額
                    adjustment_0107 = stats['total_amount'] - sales_total
                    
                    print(f"\n0107 支付寶分析：")
                    print(f"  WITHDRAW 總額: {stats['total_amount']:,.2f} RMB")
                    print(f"  從 0107 售出的總額: {sales_total:,.2f} RMB")
                    print(f"  錯誤扣款（需要調整）: {adjustment_0107:,.2f} RMB")
                    break
            
            # 顯示將要執行的操作
            print("\n" + "=" * 80)
            print("將要執行的操作：")
            print("=" * 80)
            
            if account_0107 and adjustment_0107 > 0:
                print(f"1. 0107 支付寶：調整餘額 +{adjustment_0107:,.2f} RMB")
                print(f"   調整前: {account_0107.balance:,.2f} RMB")
                print(f"   調整後: {account_0107.balance + adjustment_0107:,.2f} RMB")
            else:
                print("1. 0107 支付寶：無需調整（或未找到）")
            
            print("2. 其他帳戶（7773、6186 等）：餘額保持不變")
            print(f"3. 刪除所有售出扣款 WITHDRAW 記錄: {len(withdraw_records)} 筆")
            
            # 確認
            print("\n" + "=" * 80)
            response = input("是否繼續？(yes/no): ")
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return 0
            
            # 調整 0107 餘額（如果需要的話）
            if account_0107 and adjustment_0107 > 0:
                old_balance_0107 = account_0107.balance
                account_0107.balance += adjustment_0107
                new_balance_0107 = account_0107.balance
                
                print(f"\n✅ 調整 0107 支付寶餘額: +{adjustment_0107:,.2f} RMB")
                print(f"   餘額變化: {old_balance_0107:,.2f} -> {new_balance_0107:,.2f} RMB")
            
            # 驗證其他帳戶保持不變
            print("\n其他帳戶餘額驗證：")
            for account_id, stats in account_stats.items():
                account = stats['account']
                if account and account != account_0107:
                    account_name = account.name
                    print(f"  {account_name}: 保持 {account.balance:,.2f} RMB（不變）")
            
            # 刪除所有 WITHDRAW 記錄
            deleted_count = 0
            for record in withdraw_records:
                db.session.delete(record)
                deleted_count += 1
            
            db.session.commit()
            
            print("\n" + "=" * 80)
            print("✅ 清理完成！")
            print("=" * 80)
            print(f"刪除 WITHDRAW 記錄: {deleted_count} 筆")
            
            if account_0107 and adjustment_0107 > 0:
                print(f"0107 支付寶餘額調整: +{adjustment_0107:,.2f} RMB")
                print(f"  最終餘額: {account_0107.balance:,.2f} RMB")
            
            print("其他帳戶餘額：保持不變")
            print("\n以後的售出將直接從帳戶餘額扣除，不再創建 WITHDRAW 記錄")
            
            return 0
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清理失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    print("清理 WITHDRAW 記錄工具（保持帳戶餘額不變）")
    print("只調整 0107 的錯誤扣款，其他帳戶保持原樣\n")
    
    exit_code = cleanup_withdraw_no_change()
    sys.exit(exit_code)


