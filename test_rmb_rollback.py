"""
測試RMB回滾機制的驗證腳本
專門驗證買入記錄刪除時RMB帳戶是否正確回滾
"""

import sqlite3
import requests
import json
from datetime import datetime


def connect_local_db():
    """連接本地資料庫"""
    db_path = "./instance/sales_system_v4.db"
    return sqlite3.connect(db_path)


def test_rmb_rollback_scenario():
    """測試RMB回滾場景"""
    print("=" * 80)
    print("RMB回滾機制驗證測試")
    print("=" * 80)
    
    conn = connect_local_db()
    cursor = conn.cursor()
    
    try:
        # 1. 找到7773持有人的支付寶帳戶
        print("\n1. 查找7773持有人的支付寶帳戶")
        cursor.execute("""
            SELECT ca.id, ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'RMB' AND ca.name LIKE '%支付寶%'
        """)
        rmb_accounts = cursor.fetchall()
        
        print("找到的RMB支付寶帳戶：")
        for acc in rmb_accounts:
            acc_id, acc_name, balance, holder = acc
            holder_display = holder if holder else "N/A"
            print(f"   ID: {acc_id}, 持有人: {holder_display}, 帳戶: {acc_name}, 餘額: {balance}")
        
        if not rmb_accounts:
            print("   未找到RMB支付寶帳戶")
            return
        
        # 選擇第一個RMB支付寶帳戶進行測試
        test_account = rmb_accounts[0]
        test_account_id = test_account[0]
        test_account_name = test_account[1]
        current_balance = test_account[3]
        
        print(f"\n選擇測試帳戶：ID {test_account_id} ({test_account_name})")
        print(f"當前餘額：{current_balance} RMB")
        
        # 2. 檢查該帳戶的FIFO庫存
        print(f"\n2. 檢查帳戶 {test_account_name} 的FIFO庫存")
        cursor.execute("""
            SELECT 
                fi.id,
                fi.purchase_record_id,
                fi.rmb_amount,
                fi.remaining_rmb,
                pr.created_at,
                pr.rmb_amount as purchase_rmb,
                pr.twd_cost
            FROM fifo_inventory fi
            JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            WHERE pr.deposit_account_id = ?
            ORDER BY fi.purchase_date
        """, (test_account_id,))
        
        fifo_records = cursor.fetchall()
        
        if fifo_records:
            print(f"找到 {len(fifo_records)} 筆FIFO庫存記錄：")
            total_fifo_rmb = 0
            for record in fifo_records:
                fi_id, pr_id, fi_rmb, remaining, created, purchase_rmb, twd_cost = record
                total_fifo_rmb += remaining
                print(f"   FIFO ID: {fi_id}, 買入記錄ID: {pr_id}")
                print(f"   初始RMB: {fi_rmb}, 剩餘RMB: {remaining}")
                print(f"   買入RMB: {purchase_rmb}, 台幣成本: {twd_cost}")
                print(f"   創建時間: {created}")
                print()
        else:
            print("   沒有找到FIFO庫存記錄")
            total_fifo_rmb = 0
        
        print(f"FIFO庫存總計：{total_fifo_rmb} RMB")
        print(f"帳戶餘額：{current_balance} RMB")
        print(f"差異：{current_balance - total_fifo_rmb} RMB")
        
        if abs(current_balance - total_fifo_rmb) > 0.01:
            print(f"\n⚠️ 發現問題：帳戶餘額與FIFO庫存不匹配！")
            print(f"   多餘金額：{current_balance - total_fifo_rmb} RMB")
            print(f"   這很可能是因為錯誤刪除買入記錄時，RMB沒有正確回滾")
            
            # 3. 提供修復建議
            excess_amount = current_balance - total_fifo_rmb
            print(f"\n3. 修復建議")
            print(f"   應該將帳戶餘額調整為：{total_fifo_rmb} RMB")
            print(f"   需要減少：{excess_amount} RMB")
            
            # 詢問是否修復
            print(f"\n是否要修復此帳戶？")
            choice = input("請輸入 (yes/no): ").strip().lower()
            
            if choice == 'yes':
                new_balance = total_fifo_rmb
                cursor.execute(
                    "UPDATE cash_accounts SET balance = ? WHERE id = ?",
                    (new_balance, test_account_id)
                )
                conn.commit()
                print(f"✅ 已修復！帳戶餘額調整為：{new_balance} RMB")
                
                # 驗證修復結果
                cursor.execute("SELECT balance FROM cash_accounts WHERE id = ?", (test_account_id,))
                new_balance_check = cursor.fetchone()[0]
                print(f"驗證：當前餘額為：{new_balance_check} RMB")
        else:
            print(f"\n✅ 帳戶餘額與FIFO庫存匹配，沒有問題")
        
        # 4. 測試建議
        print(f"\n4. 線上測試建議")
        print(f"   在線上環境執行以下測試：")
        print(f"   1. 記下7773支付寶帳戶當前餘額")
        print(f"   2. 創建一筆小額買入記錄（如100 RMB）")
        print(f"   3. 確認RMB帳戶餘額增加了100")
        print(f"   4. 刪除該買入記錄")
        print(f"   5. 確認RMB帳戶餘額回到原始值")
        print(f"   6. 如果沒有回到原始值，說明回滾機制仍有問題")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


def create_test_purchase_and_delete():
    """創建測試買入記錄並刪除（僅用於本地測試）"""
    print("\n" + "=" * 80)
    print("本地測試：創建並刪除買入記錄")
    print("=" * 80)
    
    conn = connect_local_db()
    cursor = conn.cursor()
    
    try:
        # 找到7773持有人的帳戶
        cursor.execute("""
            SELECT ca.id, ca.name, ca.currency, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE h.name LIKE '%7773%' OR h.name LIKE '%7773%'
        """)
        accounts = cursor.fetchall()
        
        print("7773持有人的帳戶：")
        for acc in accounts:
            acc_id, acc_name, currency, holder = acc
            print(f"   ID: {acc_id}, 帳戶: {acc_name}, 幣別: {currency}")
        
        # 這裡需要手動指定帳戶ID，因為需要TWD付款帳戶和RMB收款帳戶
        print("\n注意：此測試需要手動指定帳戶ID")
        print("請在app.py中執行以下測試步驟：")
        print("1. 登入系統")
        print("2. 到買入頁面")
        print("3. 創建一筆小額測試買入（如100 RMB）")
        print("4. 記錄買入記錄ID")
        print("5. 刪除該買入記錄")
        print("6. 檢查帳戶餘額是否正確回滾")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("選擇測試模式：")
    print("1. 檢查現有帳戶餘額與FIFO庫存的一致性")
    print("2. 創建本地測試買入記錄（需要手動操作）")
    
    choice = input("請選擇 (1/2): ").strip()
    
    if choice == "1":
        test_rmb_rollback_scenario()
    elif choice == "2":
        create_test_purchase_and_delete()
    else:
        print("無效選擇，執行預設檢查")
        test_rmb_rollback_scenario()
