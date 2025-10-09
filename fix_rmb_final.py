"""
最終修復RMB帳戶餘額工具
"""

import sqlite3

def fix_rmb_accounts():
    """修復RMB帳戶餘額"""
    conn = sqlite3.connect('./instance/sales_system_v4.db')
    cursor = conn.cursor()
    
    try:
        print("開始修復RMB帳戶餘額...")
        
        # 修復帳戶ID 2 (007持有人的123帳戶)
        print("\n1. 修復帳戶ID 2 (007持有人的123帳戶)")
        print("   從 15,500.00 RMB 調整為 10,780.00 RMB")
        cursor.execute("UPDATE cash_accounts SET balance = 10780.00 WHERE id = 2")
        print("   完成")
        
        # 修復帳戶ID 4 (測試持有人的123帳戶)
        print("\n2. 修復帳戶ID 4 (測試持有人的123帳戶)")
        print("   從 9,860.00 RMB 調整為 4,510.00 RMB")
        cursor.execute("UPDATE cash_accounts SET balance = 4510.00 WHERE id = 4")
        print("   完成")
        
        # 提交變更
        conn.commit()
        print("\n所有修復完成！")
        
        # 驗證修復結果
        print("\n驗證修復結果:")
        cursor.execute("""
            SELECT ca.id, ca.name, ca.balance, h.name as holder_name
            FROM cash_accounts ca
            LEFT JOIN holders h ON ca.holder_id = h.id
            WHERE ca.id IN (2, 4)
        """)
        results = cursor.fetchall()
        for result in results:
            acc_id, acc_name, balance, holder = result
            holder_display = holder if holder else "N/A"
            print(f"   帳戶ID {acc_id} ({holder_display}-{acc_name}): {balance:,.2f} RMB")
        
        print("\n現在帳戶餘額應該與FIFO庫存匹配了！")
        
    except Exception as e:
        conn.rollback()
        print(f"修復失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("RMB帳戶餘額自動修復工具")
    print("=" * 60)
    fix_rmb_accounts()
