"""
專門修復7773支付寶帳戶多餘的4.28 RMB
"""

import sqlite3


def fix_7773_account():
    """修復7773支付寶帳戶"""
    print("=" * 80)
    print("修復7773支付寶帳戶多餘的4.28 RMB")
    print("=" * 80)
    
    print("\n問題分析：")
    print("- 7773支付寶帳戶原本餘額為0")
    print("- 錯誤刪除買入記錄時，RMB沒有正確回滾")
    print("- 現在多出了4.28 RMB")
    
    print("\n修復方案：")
    print("1. 找到7773支付寶帳戶")
    print("2. 檢查該帳戶的FIFO庫存")
    print("3. 將帳戶餘額調整為與FIFO庫存一致")
    
    # 請用戶提供資料庫路徑
    db_path = input("\n請輸入線上資料庫路徑: ").strip()
    if not db_path:
        print("❌ 未提供資料庫路徑")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n連接資料庫成功：{db_path}")
        
        # 1. 找到7773支付寶帳戶
        print("\n1. 查找7773支付寶帳戶")
        cursor.execute("""
            SELECT ca.id, ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.currency = 'RMB' 
            AND h.name LIKE '%7773%'
        """)
        
        accounts = cursor.fetchall()
        
        if not accounts:
            print("❌ 未找到7773持有人的RMB帳戶")
            print("\n嘗試查找所有RMB帳戶：")
            cursor.execute("""
                SELECT ca.id, ca.name, ca.balance, h.name as holder_name
                FROM cash_accounts ca
                LEFT JOIN holders h ON ca.holder_id = h.id
                WHERE ca.currency = 'RMB'
            """)
            all_rmb_accounts = cursor.fetchall()
            for acc in all_rmb_accounts:
                acc_id, acc_name, balance, holder = acc
                holder_display = holder if holder else "N/A"
                print(f"   ID: {acc_id}, 持有人: {holder_display}, 帳戶: {acc_name}, 餘額: {balance}")
            return
        
        print("找到的7773 RMB帳戶：")
        for acc in accounts:
            acc_id, acc_name, balance, holder = acc
            holder_display = holder if holder else "N/A"
            print(f"   ID: {acc_id}, 持有人: {holder_display}, 帳戶: {acc_name}, 餘額: {balance}")
        
        # 2. 檢查每個帳戶
        for account in accounts:
            acc_id, acc_name, balance, holder = account
            holder_display = holder if holder else "N/A"
            
            print(f"\n2. 檢查帳戶 {holder_display}-{acc_name} (ID: {acc_id})")
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
                    
                    # 確認是否修復
                    if abs(difference - 4.28) < 0.01:
                        print(f"   ✅ 這正是我們要修復的4.28 RMB問題！")
                    
                    print(f"\n   修復方案：將餘額從 {balance} 調整為 {total_fifo_rmb}")
                    confirm = input("   確認執行修復？(yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        cursor.execute(
                            "UPDATE cash_accounts SET balance = ? WHERE id = ?",
                            (total_fifo_rmb, acc_id)
                        )
                        conn.commit()
                        print(f"   ✅ 修復完成！餘額已調整為 {total_fifo_rmb} RMB")
                        
                        # 驗證
                        cursor.execute("SELECT balance FROM cash_accounts WHERE id = ?", (acc_id,))
                        new_balance = cursor.fetchone()[0]
                        print(f"   驗證：當前餘額為 {new_balance} RMB")
                        
                        if abs(new_balance - total_fifo_rmb) < 0.01:
                            print(f"   🎉 修復成功！帳戶餘額現在與FIFO庫存一致")
                        else:
                            print(f"   ❌ 修復可能失敗，請檢查")
                    else:
                        print("   ❌ 取消修復")
                else:
                    print(f"   ⚠️ 不足金額：{abs(difference)} RMB")
                    print(f"   這可能是其他問題，建議手動檢查")
            else:
                print(f"   ✅ 帳戶餘額與FIFO庫存匹配，無需修復")
        
        print("\n" + "=" * 80)
        print("修復完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    fix_7773_account()
