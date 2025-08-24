#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查帳戶帳本記錄工具
幫助用戶了解為什麼無法刪除帳戶
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_account_records():
    """檢查帳戶的帳本記錄"""
    print("🔍 檢查帳戶帳本記錄工具")
    print("=" * 50)
    
    try:
        # 導入必要的模組
        from app import app, db, CashAccount, LedgerEntry, CashLog, SalesRecord, Transaction, PurchaseRecord
        
        with app.app_context():
            print("📊 檢查所有帳戶的帳本記錄...")
            print()
            
            # 查詢所有帳戶
            accounts = db.session.execute(db.select(CashAccount)).scalars().all()
            
            for account in accounts:
                print(f"🏦 帳戶: {account.name} (ID: {account.id}, 幣別: {account.currency})")
                print(f"   持有人: {account.holder.name if account.holder else 'N/A'}")
                print(f"   餘額: {account.balance:,.2f}")
                print(f"   狀態: {'啟用' if account.is_active else '停用'}")
                
                # 檢查 LedgerEntry 記錄
                ledger_entries = db.session.execute(
                    db.select(LedgerEntry).filter(LedgerEntry.account_id == account.id)
                ).scalars().all()
                
                if ledger_entries:
                    print(f"   📝 帳本記錄: {len(ledger_entries)} 筆")
                    for entry in ledger_entries[:3]:  # 只顯示前3筆
                        print(f"      - {entry.entry_date.strftime('%Y-%m-%d %H:%M')} | {entry.entry_type} | {entry.amount:,.2f} | {entry.description}")
                    if len(ledger_entries) > 3:
                        print(f"      ... 還有 {len(ledger_entries) - 3} 筆記錄")
                else:
                    print("   📝 帳本記錄: 0 筆")
                
                # 檢查現金流水記錄
                cash_logs = db.session.execute(
                    db.select(CashLog).filter(CashLog.type == "SETTLEMENT")
                ).scalars().all()
                
                # 檢查是否有與此帳戶相關的現金流水（通過描述匹配）
                related_cash_logs = [log for log in cash_logs if account.name in log.description]
                
                if related_cash_logs:
                    print(f"   💰 相關現金流水: {len(related_cash_logs)} 筆")
                    for log in related_cash_logs[:3]:  # 只顯示前3筆
                        print(f"      - {log.time.strftime('%Y-%m-%d %H:%M')} | {log.type} | {log.amount:,.2f} | {log.description}")
                    if len(related_cash_logs) > 3:
                        print(f"      ... 還有 {len(related_cash_logs) - 3} 筆記錄")
                else:
                    print("   💰 相關現金流水: 0 筆")
                
                # 檢查是否可以刪除
                can_delete = True
                reasons = []
                
                if account.balance != 0:
                    can_delete = False
                    reasons.append(f"帳戶餘額不為0 ({account.balance:,.2f})")
                
                if ledger_entries:
                    can_delete = False
                    reasons.append(f"有 {len(ledger_entries)} 筆帳本記錄")
                
                if can_delete:
                    print("   ✅ 可以刪除")
                else:
                    print(f"   ❌ 無法刪除: {', '.join(reasons)}")
                
                print("-" * 50)
            
            # 特別檢查有問題的帳戶
            print("\n🔍 特別檢查 - 無法刪除的帳戶:")
            print("=" * 50)
            
            for account in accounts:
                ledger_count = db.session.execute(
                    db.select(func.count(LedgerEntry.id)).filter(LedgerEntry.account_id == account.id)
                ).scalar()
                
                if account.balance != 0 or ledger_count > 0:
                    print(f"❌ 帳戶 '{account.name}' 無法刪除:")
                    print(f"   餘額: {account.balance:,.2f}")
                    print(f"   帳本記錄: {ledger_count} 筆")
                    
                    if ledger_count > 0:
                        print("   建議處理方式:")
                        print("   1. 檢查帳本記錄的內容")
                        print("   2. 如果記錄不再需要，可以考慮清理")
                        print("   3. 或者將帳戶設為停用而非刪除")
                    
                    print()
            
            print("✅ 檢查完成！")
            
    except ImportError as e:
        print(f"❌ 導入模組失敗: {e}")
        print("請確保在正確的環境中運行此腳本")
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def show_account_details(account_id):
    """顯示特定帳戶的詳細資訊"""
    try:
        from app import app, db, CashAccount, LedgerEntry
        
        with app.app_context():
            account = db.session.get(CashAccount, account_id)
            if not account:
                print(f"❌ 找不到ID為 {account_id} 的帳戶")
                return
            
            print(f"🔍 帳戶詳細資訊: {account.name}")
            print("=" * 50)
            print(f"ID: {account.id}")
            print(f"名稱: {account.name}")
            print(f"幣別: {account.currency}")
            print(f"餘額: {account.balance:,.2f}")
            print(f"持有人: {account.holder.name if account.holder else 'N/A'}")
            print(f"狀態: {'啟用' if account.is_active else '停用'}")
            
            # 顯示帳本記錄
            ledger_entries = db.session.execute(
                db.select(LedgerEntry).filter(LedgerEntry.account_id == account.id)
            ).scalars().all()
            
            print(f"\n📝 帳本記錄 ({len(ledger_entries)} 筆):")
            if ledger_entries:
                for i, entry in enumerate(ledger_entries, 1):
                    print(f"{i:2d}. {entry.entry_date.strftime('%Y-%m-%d %H:%M')} | {entry.entry_type} | {entry.amount:,.2f}")
                    print(f"    描述: {entry.description}")
                    print(f"    操作員: {entry.operator.username if entry.operator else 'N/A'}")
                    print()
            else:
                print("   無帳本記錄")
            
            # 檢查是否可以刪除
            can_delete = True
            reasons = []
            
            if account.balance != 0:
                can_delete = False
                reasons.append(f"帳戶餘額不為0 ({account.balance:,.2f})")
            
            if ledger_entries:
                can_delete = False
                reasons.append(f"有 {len(ledger_entries)} 筆帳本記錄")
            
            print("🗑️  刪除狀態:")
            if can_delete:
                print("   ✅ 可以刪除")
            else:
                print(f"   ❌ 無法刪除: {', '.join(reasons)}")
                
                if ledger_entries:
                    print("\n💡 處理建議:")
                    print("   1. 檢查帳本記錄是否仍需要")
                    print("   2. 如果記錄不再需要，可以考慮清理")
                    print("   3. 或者將帳戶設為停用而非刪除")
                    print("   4. 聯繫系統管理員協助處理")
            
    except Exception as e:
        print(f"❌ 顯示帳戶詳細資訊時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            account_id = int(sys.argv[1])
            show_account_details(account_id)
        except ValueError:
            print("❌ 帳戶ID必須是數字")
            print("使用方法: python check_account_records.py [帳戶ID]")
    else:
        check_account_records()
