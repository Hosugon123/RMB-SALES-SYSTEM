"""
自動修復RMB帳戶餘額工具
"""

import sqlite3

def fix_rmb_accounts():
    """修復RMB帳戶餘額"""
    conn = sqlite3.connect('./instance/sales_system_v4.db')
    cursor = conn.cursor()
    
    try:
        # 修復帳戶ID 2 (007持有人的123帳戶)
        print("修復帳戶ID 2 (007持有人的123帳戶)")
        print("  當前餘額: 15,500.00 RMB")
        print("  應該餘額: 10,780.00 RMB")
        print("  需要減少: 4,720.00 RMB")
        
        cursor.execute("UPDATE cash_accounts SET balance = 10780.00 WHERE id = 2")
        print("  ✅ 已修復")
        
        # 修復帳戶ID 4 (測試持有人的123帳戶)
        print("\n修復帳戶ID 4 (測試持有人的123帳戶)")
        print("  當前餘額: 9,860.00 RMB")
        print("  應該餘額: 4,510.00 RMB")
        print("  需要減少: 5,350.00 RMB")
        
        cursor.execute("UPDATE cash_accounts SET balance = 4510.00 WHERE id = 4")
        print("  ✅ 已修復")
        
        # 提交變更
        conn.commit()
        print("\n🎉 所有修復完成！")
        
        # 驗證修復結果
        print("\n驗證修復結果:")
        cursor.execute("SELECT id, name, balance FROM cash_accounts WHERE id IN (2, 4)")
        results = cursor.fetchall()
        for result in results:
            print(f"  帳戶ID {result[0]} ({result[1]}): {result[2]:,.2f} RMB")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 修復失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("RMB帳戶餘額自動修復工具")
    print("=" * 60)
    print()
    print("即將修復以下帳戶:")
    print("1. 帳戶ID 2: 15,500.00 → 10,780.00 RMB (減少4,720)")
    print("2. 帳戶ID 4: 9,860.00 → 4,510.00 RMB (減少5,350)")
    print()
    
    confirm = input("確認執行修復？(yes/no): ").strip().lower()
    
    if confirm == 'yes':
        fix_rmb_accounts()
    else:
        print("❌ 取消修復")
