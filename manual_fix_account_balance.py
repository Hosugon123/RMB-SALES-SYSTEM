"""
手動修正帳戶餘額工具

如果您知道哪些台幣帳戶需要修正，但不確定具體被刪除的記錄，
可以使用此工具直接調整帳戶餘額。

使用場景：
1. 沒有完整的備份資料庫
2. 知道大概需要調整的金額
3. 想要快速修復帳戶餘額

注意：此工具會直接修改資料庫，請謹慎使用！
"""

import sqlite3
import os
from datetime import datetime


def connect_db(db_path):
    """連接資料庫"""
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫: {db_path}")
        return None
    return sqlite3.connect(db_path)


def list_all_accounts(conn):
    """列出所有帳戶"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.id, ca.name, ca.currency, ca.balance, h.name as holder_name
        FROM cash_accounts ca
        LEFT JOIN holders h ON ca.holder_id = h.id
        WHERE ca.is_active = 1
        ORDER BY ca.currency, h.name, ca.name
    """)
    accounts = cursor.fetchall()
    return accounts


def display_accounts(accounts):
    """顯示帳戶列表"""
    print("\n" + "=" * 100)
    print("當前活躍帳戶列表")
    print("=" * 100)
    print(f"{'ID':<5} {'持有人':<15} {'帳戶名稱':<30} {'幣別':<5} {'餘額':<20}")
    print("-" * 100)
    
    for account in accounts:
        account_id, name, currency, balance, holder_name = account
        holder_display = holder_name if holder_name else "N/A"
        print(f"{account_id:<5} {holder_display:<15} {name:<30} {currency:<5} {balance:>18,.2f}")
    
    print("=" * 100)


def adjust_account_balance(conn, account_id, adjustment_amount, reason):
    """調整帳戶餘額"""
    cursor = conn.cursor()
    
    # 獲取當前餘額
    cursor.execute("SELECT name, balance, currency FROM cash_accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ 找不到帳戶 ID: {account_id}")
        return False
    
    account_name, current_balance, currency = result
    new_balance = current_balance + adjustment_amount
    
    print(f"\n📝 準備調整帳戶: {account_name} ({currency})")
    print(f"   當前餘額: {current_balance:,.2f}")
    print(f"   調整金額: {adjustment_amount:+,.2f}")
    print(f"   調整後餘額: {new_balance:,.2f}")
    print(f"   原因: {reason}")
    
    confirm = input("\n確認執行此調整？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ 取消調整")
        return False
    
    try:
        # 更新餘額
        cursor.execute(
            "UPDATE cash_accounts SET balance = ? WHERE id = ?",
            (new_balance, account_id)
        )
        
        # 創建記錄日誌（如果有ledger_entries表）
        try:
            cursor.execute("""
                INSERT INTO ledger_entries (entry_type, account_id, amount, description, operator_id, entry_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'ADJUSTMENT' if adjustment_amount > 0 else 'ADJUSTMENT',
                account_id,
                abs(adjustment_amount),
                f"手動修正：{reason}",
                1,  # 系統用戶ID
                datetime.now()
            ))
            print("✅ 已創建流水記錄")
        except Exception as e:
            print(f"⚠️ 無法創建流水記錄（這是正常的）: {e}")
        
        conn.commit()
        print("✅ 帳戶餘額調整完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 調整失敗: {e}")
        return False


def main():
    """主程序"""
    print("=" * 100)
    print("手動修正帳戶餘額工具")
    print("=" * 100)
    print()
    print("⚠️ 重要提醒：")
    print("   1. 此工具會直接修改資料庫")
    print("   2. 請先備份資料庫")
    print("   3. 建議在測試環境先驗證")
    print()
    
    # 獲取資料庫路徑
    db_path = input("請輸入資料庫路徑 (預設: ./instance/sales_system.db): ").strip()
    if not db_path:
        db_path = "./instance/sales_system.db"
    
    # 連接資料庫
    conn = connect_db(db_path)
    if not conn:
        return
    
    try:
        while True:
            # 列出所有帳戶
            accounts = list_all_accounts(conn)
            display_accounts(accounts)
            
            print("\n選項：")
            print("1. 調整帳戶餘額")
            print("2. 刷新帳戶列表")
            print("3. 退出")
            
            choice = input("\n請選擇操作 (1-3): ").strip()
            
            if choice == '1':
                # 調整帳戶餘額
                print("\n" + "=" * 100)
                print("調整帳戶餘額")
                print("=" * 100)
                
                try:
                    account_id = int(input("請輸入帳戶ID: ").strip())
                    adjustment_amount = float(input("請輸入調整金額 (正數為增加，負數為減少): ").strip())
                    reason = input("請輸入調整原因: ").strip()
                    
                    if not reason:
                        reason = "手動修正帳戶餘額"
                    
                    adjust_account_balance(conn, account_id, adjustment_amount, reason)
                    
                except ValueError:
                    print("❌ 輸入格式錯誤，請重試")
                except Exception as e:
                    print(f"❌ 發生錯誤: {e}")
                
                input("\n按Enter繼續...")
                
            elif choice == '2':
                # 刷新列表
                continue
                
            elif choice == '3':
                # 退出
                print("\n再見！")
                break
                
            else:
                print("❌ 無效的選擇，請重試")
                input("\n按Enter繼續...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷操作")
    
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print("\n資料庫連接已關閉")


if __name__ == "__main__":
    main()


