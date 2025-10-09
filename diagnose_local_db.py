"""
本地資料庫診斷工具

用於診斷和修復已刪除買入記錄但帳戶餘額未正確回滾的問題
"""

import sqlite3
from datetime import datetime


def connect_local_db():
    """連接本地資料庫"""
    db_path = "./instance/sales_system.db"
    return sqlite3.connect(db_path)


def list_accounts_with_balance(conn):
    """列出所有有餘額的帳戶"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ca.id, ca.name, ca.currency, ca.balance, h.name as holder_name
        FROM cash_accounts ca
        LEFT JOIN holders h ON ca.holder_id = h.id
        WHERE ca.is_active = 1 AND ca.balance != 0
        ORDER BY ca.currency, ca.balance DESC
    """)
    accounts = cursor.fetchall()
    return accounts


def check_fifo_inventory(conn):
    """檢查FIFO庫存狀態"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            fi.id,
            fi.purchase_record_id,
            fi.initial_rmb,
            fi.remaining_rmb,
            fi.cost_per_rmb,
            fi.purchase_date
        FROM fifo_inventory fi
        WHERE fi.remaining_rmb > 0
        ORDER BY fi.purchase_date
    """)
    inventory = cursor.fetchall()
    return inventory


def check_purchase_records(conn):
    """檢查買入記錄"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pr.id,
            pr.payment_account_id,
            pr.deposit_account_id,
            pr.rmb_amount,
            pr.twd_cost,
            pr.exchange_rate,
            pr.created_at,
            pa.name as payment_account,
            da.name as deposit_account
        FROM purchase_records pr
        LEFT JOIN cash_accounts pa ON pr.payment_account_id = pa.id
        LEFT JOIN cash_accounts da ON pr.deposit_account_id = da.id
        ORDER BY pr.created_at DESC
        LIMIT 20
    """)
    records = cursor.fetchall()
    return records


def verify_rmb_account_balance(conn, account_id):
    """驗證RMB帳戶餘額是否與FIFO庫存匹配"""
    cursor = conn.cursor()
    
    # 獲取帳戶餘額
    cursor.execute("""
        SELECT name, balance, currency
        FROM cash_accounts
        WHERE id = ?
    """, (account_id,))
    account = cursor.fetchone()
    
    if not account:
        print(f"❌ 找不到帳戶 ID: {account_id}")
        return None
    
    account_name, account_balance, currency = account
    
    if currency != 'RMB':
        print(f"⚠️ 帳戶 {account_name} 不是RMB帳戶")
        return None
    
    # 計算該帳戶對應的FIFO庫存總額
    cursor.execute("""
        SELECT SUM(fi.remaining_rmb) as total_fifo_rmb
        FROM fifo_inventory fi
        JOIN purchase_records pr ON fi.purchase_record_id = pr.id
        WHERE pr.deposit_account_id = ?
    """, (account_id,))
    
    result = cursor.fetchone()
    total_fifo_rmb = result[0] if result[0] else 0
    
    print(f"\n📊 帳戶分析: {account_name} (ID: {account_id})")
    print(f"   幣別: {currency}")
    print(f"   帳戶餘額: ¥{account_balance:,.2f}")
    print(f"   FIFO庫存總額: ¥{total_fifo_rmb:,.2f}")
    print(f"   差異: ¥{account_balance - total_fifo_rmb:,.2f}")
    
    if abs(account_balance - total_fifo_rmb) > 0.01:
        print(f"   ⚠️ 警告：帳戶餘額與FIFO庫存不匹配！")
        print(f"   可能原因：")
        print(f"   1. 買入記錄被刪除但餘額未回滾")
        print(f"   2. 有外部存款（獨立儲值）")
        print(f"   3. 有純利潤庫存（手續費）")
        return {
            'account_id': account_id,
            'account_name': account_name,
            'account_balance': account_balance,
            'fifo_balance': total_fifo_rmb,
            'difference': account_balance - total_fifo_rmb
        }
    else:
        print(f"   ✅ 帳戶餘額與FIFO庫存匹配")
        return None


def manual_adjust_account(conn, account_id, adjustment_amount, reason):
    """手動調整帳戶餘額"""
    cursor = conn.cursor()
    
    # 獲取當前餘額
    cursor.execute("SELECT name, balance, currency FROM cash_accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ 找不到帳戶 ID: {account_id}")
        return False
    
    account_name, current_balance, currency = result
    new_balance = current_balance + adjustment_amount
    
    print(f"\n📝 準備調整帳戶")
    print(f"   帳戶: {account_name} ({currency})")
    print(f"   當前餘額: {current_balance:,.2f}")
    print(f"   調整金額: {adjustment_amount:+,.2f}")
    print(f"   調整後餘額: {new_balance:,.2f}")
    print(f"   原因: {reason}")
    
    try:
        # 更新餘額
        cursor.execute(
            "UPDATE cash_accounts SET balance = ? WHERE id = ?",
            (new_balance, account_id)
        )
        conn.commit()
        print("✅ 調整完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 調整失敗: {e}")
        return False


def main():
    """主程序"""
    print("=" * 100)
    print("本地資料庫診斷工具")
    print("=" * 100)
    print()
    
    conn = connect_local_db()
    
    try:
        # 1. 列出所有帳戶
        print("\n1️⃣ 當前帳戶餘額狀態")
        print("=" * 100)
        accounts = list_accounts_with_balance(conn)
        
        print(f"{'ID':<5} {'持有人':<15} {'帳戶名稱':<30} {'幣別':<5} {'餘額':<20}")
        print("-" * 100)
        for acc in accounts:
            acc_id, name, currency, balance, holder = acc
            holder_display = holder if holder else "N/A"
            print(f"{acc_id:<5} {holder_display:<15} {name:<30} {currency:<5} {balance:>18,.2f}")
        
        # 2. 列出FIFO庫存
        print("\n\n2️⃣ 當前FIFO庫存狀態")
        print("=" * 100)
        inventory = check_fifo_inventory(conn)
        
        if inventory:
            print(f"{'庫存ID':<8} {'買入記錄ID':<12} {'初始RMB':<15} {'剩餘RMB':<15} {'成本匯率':<12} {'買入日期':<20}")
            print("-" * 100)
            total_remaining = 0
            for inv in inventory:
                inv_id, pr_id, initial, remaining, cost, date = inv
                total_remaining += remaining
                print(f"{inv_id:<8} {pr_id:<12} {initial:>13,.2f} {remaining:>13,.2f} {cost:>10,.4f} {date:<20}")
            print("-" * 100)
            print(f"{'FIFO庫存總計:':<40} {total_remaining:>13,.2f} RMB")
        else:
            print("⚠️ 沒有FIFO庫存記錄")
        
        # 3. 列出最近的買入記錄
        print("\n\n3️⃣ 最近的買入記錄")
        print("=" * 100)
        records = check_purchase_records(conn)
        
        if records:
            print(f"{'ID':<5} {'付款帳戶':<20} {'收款帳戶':<20} {'RMB金額':<15} {'台幣成本':<15} {'匯率':<10}")
            print("-" * 100)
            for rec in records:
                rec_id, pay_id, dep_id, rmb, twd, rate, created, pay_name, dep_name = rec
                pay_display = pay_name if pay_name else "N/A"
                dep_display = dep_name if dep_name else "N/A"
                print(f"{rec_id:<5} {pay_display:<20} {dep_display:<20} {rmb:>13,.2f} {twd:>13,.2f} {rate:>8,.4f}")
        else:
            print("⚠️ 沒有買入記錄")
        
        # 4. 檢查每個RMB帳戶
        print("\n\n4️⃣ RMB帳戶一致性檢查")
        print("=" * 100)
        
        rmb_accounts = [acc for acc in accounts if acc[2] == 'RMB']
        discrepancies = []
        
        for acc in rmb_accounts:
            acc_id = acc[0]
            result = verify_rmb_account_balance(conn, acc_id)
            if result:
                discrepancies.append(result)
        
        # 5. 提供修復建議
        if discrepancies:
            print("\n\n5️⃣ 發現問題並提供修復建議")
            print("=" * 100)
            
            for disc in discrepancies:
                print(f"\n帳戶: {disc['account_name']} (ID: {disc['account_id']})")
                print(f"   帳戶餘額: ¥{disc['account_balance']:,.2f}")
                print(f"   FIFO庫存: ¥{disc['fifo_balance']:,.2f}")
                print(f"   多餘金額: ¥{disc['difference']:,.2f}")
                print(f"\n   建議修復操作：")
                print(f"   1. 如果這是錯誤刪除買入記錄造成的，應該減少帳戶餘額")
                print(f"      調整金額: -{disc['difference']:.2f}")
                print(f"   2. 如果這是外部存款或純利潤庫存，則餘額正確")
                
                # 詢問是否要修復
                print(f"\n   是否要修正此帳戶？")
                choice = input("   請輸入 (yes/no): ").strip().lower()
                
                if choice == 'yes':
                    # 確認調整金額
                    print(f"\n   將扣除 ¥{disc['difference']:.2f}，請確認")
                    confirm = input("   確定執行？(yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        manual_adjust_account(
                            conn,
                            disc['account_id'],
                            -disc['difference'],
                            "修復買入記錄刪除後帳戶餘額未回滾問題"
                        )
                        
                        # 重新驗證
                        print("\n   重新驗證...")
                        verify_rmb_account_balance(conn, disc['account_id'])
        else:
            print("\n✅ 所有RMB帳戶餘額與FIFO庫存匹配，沒有發現問題")
        
        print("\n" + "=" * 100)
        print("診斷完成！")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()


