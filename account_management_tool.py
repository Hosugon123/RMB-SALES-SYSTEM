#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帳戶管理工具
提供帳戶停用、清理記錄等選項，幫助用戶處理無法刪除的帳戶
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_menu():
    """顯示主選單"""
    print("\n🔧 帳戶管理工具")
    print("=" * 50)
    print("1. 檢查所有帳戶狀態")
    print("2. 檢查特定帳戶詳細資訊")
    print("3. 停用帳戶（而非刪除）")
    print("4. 清理帳戶的帳本記錄（危險操作）")
    print("5. 轉移帳戶餘額到其他帳戶")
    print("6. 退出")
    print("=" * 50)

def check_all_accounts():
    """檢查所有帳戶狀態"""
    try:
        from app import app, db, CashAccount, LedgerEntry
        from sqlalchemy import func
        
        with app.app_context():
            print("\n📊 所有帳戶狀態檢查")
            print("=" * 60)
            
            accounts = db.session.execute(db.select(CashAccount)).scalars().all()
            
            for account in accounts:
                # 檢查帳本記錄數量
                ledger_count = db.session.execute(
                    db.select(func.count(LedgerEntry.id)).filter(LedgerEntry.account_id == account.id)
                ).scalar()
                
                status = "🟢 正常" if account.is_active else "🔴 已停用"
                balance_status = "💰 有餘額" if account.balance != 0 else "💸 無餘額"
                ledger_status = f"📝 {ledger_count}筆記錄" if ledger_count > 0 else "📝 無記錄"
                
                print(f"{account.id:3d} | {account.name:15s} | {account.currency:5s} | {account.balance:10,.2f} | {status} | {balance_status} | {ledger_status}")
            
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ 檢查帳戶狀態時發生錯誤: {e}")

def check_specific_account():
    """檢查特定帳戶詳細資訊"""
    try:
        account_id = input("\n請輸入帳戶ID: ").strip()
        if not account_id:
            print("❌ 帳戶ID不能為空")
            return
        
        account_id = int(account_id)
        
        from app import app, db, CashAccount, LedgerEntry
        
        with app.app_context():
            account = db.session.get(CashAccount, account_id)
            if not account:
                print(f"❌ 找不到ID為 {account_id} 的帳戶")
                return
            
            print(f"\n🔍 帳戶詳細資訊: {account.name}")
            print("=" * 60)
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
                
    except ValueError:
        print("❌ 帳戶ID必須是數字")
    except Exception as e:
        print(f"❌ 檢查帳戶詳細資訊時發生錯誤: {e}")

def disable_account():
    """停用帳戶（而非刪除）"""
    try:
        account_id = input("\n請輸入要停用的帳戶ID: ").strip()
        if not account_id:
            print("❌ 帳戶ID不能為空")
            return
        
        account_id = int(account_id)
        
        from app import app, db, CashAccount
        
        with app.app_context():
            account = db.session.get(CashAccount, account_id)
            if not account:
                print(f"❌ 找不到ID為 {account_id} 的帳戶")
                return
            
            if not account.is_active:
                print(f"❌ 帳戶 '{account.name}' 已經停用了")
                return
            
            # 確認操作
            confirm = input(f"確定要停用帳戶 '{account.name}' 嗎？(y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ 操作已取消")
                return
            
            # 停用帳戶
            account.is_active = False
            db.session.commit()
            
            print(f"✅ 帳戶 '{account.name}' 已成功停用")
            
    except ValueError:
        print("❌ 帳戶ID必須是數字")
    except Exception as e:
        print(f"❌ 停用帳戶時發生錯誤: {e}")

def clean_ledger_records():
    """清理帳戶的帳本記錄（危險操作）"""
    try:
        account_id = input("\n⚠️  警告：此操作將永久刪除帳戶的所有帳本記錄！\n請輸入要清理的帳戶ID: ").strip()
        if not account_id:
            print("❌ 帳戶ID不能為空")
            return
        
        account_id = int(account_id)
        
        from app import app, db, CashAccount, LedgerEntry
        
        with app.app_context():
            account = db.session.get(CashAccount, account_id)
            if not account:
                print(f"❌ 找不到ID為 {account_id} 的帳戶")
                return
            
            # 檢查帳本記錄
            ledger_entries = db.session.execute(
                db.select(LedgerEntry).filter(LedgerEntry.account_id == account.id)
            ).scalars().all()
            
            if not ledger_entries:
                print(f"❌ 帳戶 '{account.name}' 沒有帳本記錄需要清理")
                return
            
            print(f"\n📝 帳戶 '{account.name}' 有 {len(ledger_entries)} 筆帳本記錄:")
            for i, entry in enumerate(ledger_entries[:5], 1):
                print(f"{i}. {entry.entry_date.strftime('%Y-%m-%d %H:%M')} | {entry.entry_type} | {entry.amount:,.2f}")
                print(f"   描述: {entry.description}")
            
            if len(ledger_entries) > 5:
                print(f"... 還有 {len(ledger_entries) - 5} 筆記錄")
            
            # 多重確認
            print(f"\n⚠️  危險操作警告:")
            print(f"1. 此操作將永久刪除 {len(ledger_entries)} 筆帳本記錄")
            print(f"2. 刪除後無法恢復")
            print(f"3. 可能影響系統的審計追蹤")
            
            confirm1 = input("您確定要繼續嗎？(y/N): ").strip().lower()
            if confirm1 != 'y':
                print("❌ 操作已取消")
                return
            
            confirm2 = input("請再次輸入 'DELETE' 確認: ").strip()
            if confirm2 != 'DELETE':
                print("❌ 確認字串不匹配，操作已取消")
                return
            
            # 執行清理
            try:
                deleted_count = db.session.execute(
                    db.delete(LedgerEntry).where(LedgerEntry.account_id == account.id)
                ).rowcount
                
                db.session.commit()
                print(f"✅ 成功清理 {deleted_count} 筆帳本記錄")
                print(f"現在帳戶 '{account.name}' 應該可以刪除了")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ 清理帳本記錄時發生錯誤: {e}")
            
    except ValueError:
        print("❌ 帳戶ID必須是數字")
    except Exception as e:
        print(f"❌ 清理帳本記錄時發生錯誤: {e}")

def transfer_balance():
    """轉移帳戶餘額到其他帳戶"""
    try:
        from_account_id = input("\n請輸入要轉出餘額的帳戶ID: ").strip()
        if not from_account_id:
            print("❌ 帳戶ID不能為空")
            return
        
        from_account_id = int(from_account_id)
        
        to_account_id = input("請輸入要轉入餘額的帳戶ID: ").strip()
        if not to_account_id:
            print("❌ 目標帳戶ID不能為空")
            return
        
        to_account_id = int(to_account_id)
        
        if from_account_id == to_account_id:
            print("❌ 不能轉移到同一個帳戶")
            return
        
        from app import app, db, CashAccount
        
        with app.app_context():
            from_account = db.session.get(CashAccount, from_account_id)
            to_account = db.session.get(CashAccount, to_account_id)
            
            if not from_account:
                print(f"❌ 找不到ID為 {from_account_id} 的來源帳戶")
                return
            
            if not to_account:
                print(f"❌ 找不到ID為 {to_account_id} 的目標帳戶")
                return
            
            if from_account.balance == 0:
                print(f"❌ 來源帳戶 '{from_account.name}' 餘額為0，無需轉移")
                return
            
            if from_account.currency != to_account.currency:
                print(f"❌ 幣別不匹配：來源帳戶是 {from_account.currency}，目標帳戶是 {to_account.currency}")
                return
            
            print(f"\n💰 餘額轉移詳情:")
            print(f"來源帳戶: {from_account.name} (餘額: {from_account.balance:,.2f} {from_account.currency})")
            print(f"目標帳戶: {to_account.name} (餘額: {to_account.balance:,.2f} {to_account.currency})")
            print(f"轉移金額: {from_account.balance:,.2f} {from_account.currency}")
            
            # 確認操作
            confirm = input("確定要執行餘額轉移嗎？(y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ 操作已取消")
                return
            
            # 執行轉移
            try:
                transfer_amount = from_account.balance
                from_account.balance = 0
                to_account.balance += transfer_amount
                
                db.session.commit()
                
                print(f"✅ 餘額轉移成功！")
                print(f"來源帳戶 '{from_account.name}' 餘額: 0.00 {from_account.currency}")
                print(f"目標帳戶 '{to_account.name}' 餘額: {to_account.balance:,.2f} {to_account.currency}")
                print(f"現在來源帳戶應該可以刪除了")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ 餘額轉移時發生錯誤: {e}")
            
    except ValueError:
        print("❌ 帳戶ID必須是數字")
    except Exception as e:
        print(f"❌ 餘額轉移時發生錯誤: {e}")

def main():
    """主函數"""
    print("🔧 帳戶管理工具啟動")
    print("此工具可以幫助您處理無法刪除的帳戶問題")
    
    while True:
        try:
            show_menu()
            choice = input("請選擇操作 (1-6): ").strip()
            
            if choice == '1':
                check_all_accounts()
            elif choice == '2':
                check_specific_account()
            elif choice == '3':
                disable_account()
            elif choice == '4':
                clean_ledger_records()
            elif choice == '5':
                transfer_balance()
            elif choice == '6':
                print("👋 感謝使用帳戶管理工具！")
                break
            else:
                print("❌ 無效的選擇，請輸入 1-6")
            
            input("\n按 Enter 鍵繼續...")
            
        except KeyboardInterrupt:
            print("\n\n👋 程式被用戶中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 發生未預期的錯誤: {e}")
            input("按 Enter 鍵繼續...")

if __name__ == "__main__":
    main()
