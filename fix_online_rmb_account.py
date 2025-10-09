"""
修復線上7773支付寶帳戶多餘的4.28 RMB
"""

import sqlite3
from datetime import datetime


def fix_online_rmb_account():
    """修復線上RMB帳戶"""
    print("=" * 80)
    print("修復線上7773支付寶帳戶多餘的4.28 RMB")
    print("=" * 80)
    
    print("\n注意事項：")
    print("1. 此腳本需要在線上環境執行")
    print("2. 執行前請先備份資料庫")
    print("3. 確認7773支付寶帳戶確實多出了4.28 RMB")
    
    # 請用戶確認
    print("\n請確認：")
    print("- 7773支付寶帳戶當前餘額確實是4.28 RMB")
    print("- 原本餘額應該是0 RMB")
    print("- 多出的4.28 RMB是因為錯誤刪除買入記錄造成的")
    
    confirm = input("\n確認執行修復？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ 取消修復")
        return
    
    # 執行修復
    try:
        # 這裡需要連接線上資料庫
        # 請根據實際情況修改資料庫路徑
        db_path = input("\n請輸入線上資料庫路徑（例：./instance/sales_system.db）: ").strip()
        if not db_path:
            print("❌ 未提供資料庫路徑")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 找到7773支付寶帳戶
        print("\n1. 查找7773支付寶帳戶")
        cursor.execute("""
            SELECT ca.id, ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'RMB' 
            AND (ca.name LIKE '%支付寶%' OR ca.name LIKE '%7773%')
            AND h.name LIKE '%7773%'
        """)
        
        accounts = cursor.fetchall()
        
        if not accounts:
            print("❌ 未找到7773支付寶帳戶")
            return
        
        print("找到的帳戶：")
        for acc in accounts:
            acc_id, acc_name, balance, holder = acc
            holder_display = holder if holder else "N/A"
            print(f"   ID: {acc_id}, 持有人: {holder_display}, 帳戶: {acc_name}, 餘額: {balance}")
        
        # 2. 檢查每個帳戶的FIFO庫存
        print("\n2. 檢查帳戶餘額與FIFO庫存的一致性")
        
        for account in accounts:
            acc_id, acc_name, balance, holder = account
            holder_display = holder if holder else "N/A"
            
            print(f"\n檢查帳戶 {holder_display}-{acc_name} (ID: {acc_id})")
            print(f"   當前餘額：{balance} RMB")
            
            # 檢查FIFO庫存
            cursor.execute("""
                SELECT SUM(fi.remaining_rmb) as total_fifo_rmb
                FROM fifo_inventory fi
                JOIN purchase_records pr ON fi.purchase_record_id = pr.id
                WHERE pr.deposit_account_id = ?
            """, (acc_id,))
            
            result = cursor.fetchone()
            total_fifo_rmb = result[0] if result[0] else 0
            
            print(f"   FIFO庫存總計：{total_fifo_rmb} RMB")
            
            difference = balance - total_fifo_rmb
            print(f"   差異：{difference} RMB")
            
            if abs(difference) > 0.01:
                if difference > 0:
                    print(f"   ⚠️ 多餘金額：{difference} RMB")
                    print(f"   這很可能是錯誤刪除買入記錄造成的")
                    
                    # 詢問是否修復
                    print(f"\n   是否要修復此帳戶？")
                    fix_choice = input("   請輸入 (yes/no): ").strip().lower()
                    
                    if fix_choice == 'yes':
                        new_balance = total_fifo_rmb
                        print(f"   準備將餘額從 {balance} 調整為 {new_balance}")
                        
                        final_confirm = input("   確認執行？(yes/no): ").strip().lower()
                        
                        if final_confirm == 'yes':
                            cursor.execute(
                                "UPDATE cash_accounts SET balance = ? WHERE id = ?",
                                (new_balance, acc_id)
                            )
                            conn.commit()
                            print(f"   ✅ 修復完成！餘額已調整為 {new_balance} RMB")
                            
                            # 驗證修復結果
                            cursor.execute("SELECT balance FROM cash_accounts WHERE id = ?", (acc_id,))
                            new_balance_check = cursor.fetchone()[0]
                            print(f"   驗證：當前餘額為 {new_balance_check} RMB")
                        else:
                            print("   ❌ 取消修復")
                    else:
                        print("   ❌ 跳過此帳戶")
                else:
                    print(f"   ⚠️ 不足金額：{abs(difference)} RMB")
                    print(f"   這可能是其他問題，建議手動檢查")
            else:
                print(f"   ✅ 帳戶餘額與FIFO庫存匹配")
        
        print("\n🎉 修復完成！")
        print("\n建議後續操作：")
        print("1. 重新部署修復後的app.py")
        print("2. 測試刪除買入記錄功能")
        print("3. 確認未來不會再出現類似問題")
        
    except Exception as e:
        print(f"\n❌ 修復失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'conn' in locals():
            conn.close()


def create_manual_fix_sql():
    """創建手動修復SQL"""
    print("\n" + "=" * 80)
    print("手動修復SQL語句")
    print("=" * 80)
    
    print("\n如果您想手動執行SQL修復，可以使用以下語句：")
    print("\n1. 首先備份資料庫")
    print("   cp your_database.db your_database_backup.db")
    
    print("\n2. 查找7773支付寶帳戶")
    print("""   SELECT ca.id, ca.name, ca.balance, h.name as holder_name
   FROM cash_accounts ca
   LEFT JOIN holders h ON ca.holder_id = h.id
   WHERE ca.currency = 'RMB' 
   AND (ca.name LIKE '%支付寶%' OR ca.name LIKE '%7773%')
   AND h.name LIKE '%7773%';""")
    
    print("\n3. 檢查FIFO庫存")
    print("""   SELECT SUM(fi.remaining_rmb) as total_fifo_rmb
   FROM fifo_inventory fi
   JOIN purchase_records pr ON fi.purchase_record_id = pr.id
   WHERE pr.deposit_account_id = <帳戶ID>;""")
    
    print("\n4. 修復帳戶餘額（將 <帳戶ID> 和 <正確餘額> 替換為實際值）")
    print("   BEGIN TRANSACTION;")
    print("   UPDATE cash_accounts SET balance = <正確餘額> WHERE id = <帳戶ID>;")
    print("   COMMIT;")
    
    print("\n5. 驗證修復結果")
    print("   SELECT id, name, balance FROM cash_accounts WHERE id = <帳戶ID>;")


if __name__ == "__main__":
    print("選擇修復方式：")
    print("1. 互動式修復（推薦）")
    print("2. 查看手動修復SQL")
    
    choice = input("請選擇 (1/2): ").strip()
    
    if choice == "1":
        fix_online_rmb_account()
    elif choice == "2":
        create_manual_fix_sql()
    else:
        print("無效選擇，執行互動式修復")
        fix_online_rmb_account()
