"""
檢查7773支付寶帳戶的RMB回滾問題
"""

import sqlite3


def check_7773_account():
    """檢查7773支付寶帳戶"""
    print("=" * 80)
    print("檢查7773支付寶帳戶的RMB回滾問題")
    print("=" * 80)
    
    conn = sqlite3.connect('./instance/sales_system_v4.db')
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
        
        # 檢查每個RMB支付寶帳戶
        for account in rmb_accounts:
            acc_id, acc_name, balance, holder = account
            holder_display = holder if holder else "N/A"
            
            print(f"\n2. 檢查帳戶 {holder_display}-{acc_name} (ID: {acc_id})")
            print(f"   當前餘額：{balance} RMB")
            
            # 檢查該帳戶的FIFO庫存
            cursor.execute("""
                SELECT 
                    fi.id,
                    fi.purchase_record_id,
                    fi.rmb_amount,
                    fi.remaining_rmb,
                    pr.created_at
                FROM fifo_inventory fi
                JOIN purchase_records pr ON fi.purchase_record_id = pr.id
                WHERE pr.deposit_account_id = ?
                ORDER BY fi.purchase_date
            """, (acc_id,))
            
            fifo_records = cursor.fetchall()
            
            if fifo_records:
                print(f"   找到 {len(fifo_records)} 筆FIFO庫存記錄：")
                total_fifo_rmb = 0
                for record in fifo_records:
                    fi_id, pr_id, fi_rmb, remaining, created = record
                    total_fifo_rmb += remaining
                    print(f"      FIFO ID: {fi_id}, 買入記錄ID: {pr_id}")
                    print(f"      剩餘RMB: {remaining}, 創建時間: {created}")
            else:
                print("   沒有找到FIFO庫存記錄")
                total_fifo_rmb = 0
            
            print(f"   FIFO庫存總計：{total_fifo_rmb} RMB")
            print(f"   帳戶餘額：{balance} RMB")
            
            difference = balance - total_fifo_rmb
            print(f"   差異：{difference} RMB")
            
            if abs(difference) > 0.01:
                print(f"   ⚠️ 發現問題：帳戶餘額與FIFO庫存不匹配！")
                if difference > 0:
                    print(f"   多餘金額：{difference} RMB")
                    print(f"   這很可能是因為錯誤刪除買入記錄時，RMB沒有正確回滾")
                else:
                    print(f"   不足金額：{abs(difference)} RMB")
                    print(f"   這可能是其他問題")
            else:
                print(f"   ✅ 帳戶餘額與FIFO庫存匹配")
        
        # 3. 總結和建議
        print(f"\n3. 總結和建議")
        print(f"   如果發現多餘的RMB餘額，這正是您提到的問題：")
        print(f"   - 原本7773支付寶帳戶餘額為0")
        print(f"   - 錯誤刪除買入記錄時，RMB沒有正確回滾")
        print(f"   - 導致帳戶餘額多出了對應的金額")
        
        print(f"\n   線上測試建議：")
        print(f"   1. 部署修復後的app.py到線上")
        print(f"   2. 創建一筆小額測試買入（如100 RMB）")
        print(f"   3. 立即刪除該買入記錄")
        print(f"   4. 檢查RMB帳戶餘額是否正確回到原始值")
        print(f"   5. 如果回滾正確，說明修復成功")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == "__main__":
    check_7773_account()
