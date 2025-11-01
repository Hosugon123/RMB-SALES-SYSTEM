#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""驗證 WITHDRAW 清理邏輯是否正確"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 臨時移除環境變數中的 DATABASE_URL，強制使用本地資料庫
env_backup = None
if 'DATABASE_URL' in os.environ:
    # 如果設置了 DATABASE_URL，可以選擇使用線上資料庫
    use_online = os.environ.get('USE_ONLINE_DB', 'false').lower() == 'true'
    if not use_online:
        env_backup = os.environ['DATABASE_URL']
        del os.environ['DATABASE_URL']
else:
    env_backup = None

from app import app, db, CashAccount, SalesRecord, LedgerEntry
from sqlalchemy import func, case

def main():
    with app.app_context():
        try:
            print("=" * 100)
            print("WITHDRAW 清理驗證報告")
            print("=" * 100)
            
            # 目標帳戶
            target_account_ids = [27, 23, 31]
            target_account_names = ["0107支付寶", "7773支付寶", "6186支付寶"]
            
            print("\n【步驟1】帳戶當前餘額檢查")
            print("-" * 100)
            
            accounts_info = {}
            for account_id in target_account_ids:
                account = db.session.get(CashAccount, account_id)
                if account:
                    accounts_info[account_id] = account
                    print(f"\n帳戶 ID {account_id}: {account.name}")
                    print(f"  當前餘額: {account.balance:.2f} {account.currency}")
                else:
                    print(f"\n⚠️  帳戶 ID {account_id} 不存在！")
            
            print("\n【步驟2】售出扣款 WITHDRAW 記錄分析")
            print("-" * 100)
            
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
            ).scalars().all()
            
            print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
            
            # 按帳戶統計
            account_withdraw_stats = {}
            total_withdraw = 0
            
            for record in withdraw_records:
                account_id = record.account_id
                if account_id not in account_withdraw_stats:
                    account_withdraw_stats[account_id] = {
                        'count': 0,
                        'total': 0,
                        'account': record.account
                    }
                account_withdraw_stats[account_id]['count'] += 1
                abs_amount = abs(record.amount)
                account_withdraw_stats[account_id]['total'] += abs_amount
                total_withdraw += abs_amount
            
            for account_id, stats in account_withdraw_stats.items():
                account_name = stats['account'].name if stats['account'] else "未知帳戶"
                print(f"\n帳戶: {account_name} (ID: {account_id})")
                print(f"  WITHDRAW 記錄數量: {stats['count']} 筆")
                print(f"  WITHDRAW 總金額: {stats['total']:.2f} RMB")
            
            print(f"\n總計: {len(withdraw_records)} 筆，{total_withdraw:.2f} RMB")
            
            print("\n【步驟3】交易記錄統計")
            print("-" * 100)
            
            for account_id in target_account_ids:
                if account_id not in accounts_info:
                    continue
                    
                account = accounts_info[account_id]
                print(f"\n帳戶: {account.name} (ID: {account_id})")
                
                # 1. 買入/儲值總額
                deposit_total = db.session.execute(
                    db.select(func.sum(
                        case(
                            (LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN']), LedgerEntry.amount),
                            else_=0
                        )
                    ))
                    .filter(LedgerEntry.account_id == account_id)
                ).scalar() or 0
                
                print(f"  買入/儲值總額: {deposit_total:.2f} RMB")
                
                # 2. 售出扣款總額（來自 SalesRecord）
                sales_total = db.session.execute(
                    db.select(func.sum(SalesRecord.rmb_amount))
                    .filter(SalesRecord.rmb_account_id == account_id)
                ).scalar() or 0
                
                print(f"  銷售總額: {sales_total:.2f} RMB")
                
                # 3. 其他 WITHDRAW
                other_withdraw = db.session.execute(
                    db.select(func.sum(
                        case(
                            (
                                (LedgerEntry.entry_type == 'WITHDRAW') & 
                                (~LedgerEntry.description.like('%售出扣款%')),
                                abs(LedgerEntry.amount)
                            ),
                            else_=0
                        )
                    ))
                    .filter(LedgerEntry.account_id == account_id)
                ).scalar() or 0
                
                print(f"  其他 WITHDRAW: {other_withdraw:.2f} RMB")
                
                # 4. 售出扣款 WITHDRAW（重複記錄）
                withdraw_from_stats = account_withdraw_stats.get(account_id, {}).get('total', 0)
                print(f"  售出扣款 WITHDRAW（重複）: {withdraw_from_stats:.2f} RMB")
                
                # 5. 計算預期餘額（簡化版）
                # 假設初始餘額為0，預期餘額 = 買入 - 售出 - 其他提款
                # 注意：這只是簡化計算，實際可能更複雜
                expected_balance = deposit_total - sales_total - other_withdraw
                print(f"\n  【簡化計算預期餘額】買入 - 售出 - 其他提款")
                print(f"    預期: {expected_balance:.2f} RMB")
                print(f"    實際: {account.balance:.2f} RMB")
                print(f"    差異: {account.balance - expected_balance:.2f} RMB")
                
                # 6. 如果刪除售出扣款 WITHDRAW 後的影響
                if account_id in account_withdraw_stats:
                    after_cleanup = account.balance
                    print(f"\n  【如果刪除售出扣款 WITHDRAW】")
                    print(f"    當前餘額: {account.balance:.2f} RMB")
                    print(f"    餘額不變（不回補）")
                
                if account_id in account_withdraw_stats:
                    after_reimbursement = account.balance + withdraw_from_stats
                    print(f"\n  【如果回補售出扣款 WITHDRAW】")
                    print(f"    當前餘額: {account.balance:.2f} RMB")
                    print(f"    回補金額: +{withdraw_from_stats:.2f} RMB")
                    print(f"    回補後餘額: {after_reimbursement:.2f} RMB")
            
            print("\n【步驟4】建議")
            print("-" * 100)
            print("\n請根據以下信息判斷：")
            print("1. 如果【簡化計算預期餘額】≈【實際餘額】，建議使用 --no-reimbursement")
            print("2. 如果【實際餘額】<【預期餘額】，可能考慮回補")
            print("3. 如果不確定，強烈建議先備份資料庫並使用 --no-reimbursement")
            
            print("\n【步驟5】執行命令建議")
            print("-" * 100)
            print("\n安全方案（推薦）：")
            print("  flask cleanup-sales-withdraw --no-reimbursement --force")
            print("\n完整方案：")
            print("  flask cleanup-sales-withdraw --force")
            
        except Exception as e:
            print(f"\n驗證失敗: {e}")
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
        if env_backup:
            os.environ['DATABASE_URL'] = env_backup

