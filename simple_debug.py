import sqlite3

def simple_debug():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("🔍 開始簡單調試...")
        
        # 檢查帳戶餘額
        cursor.execute("SELECT name, currency, balance FROM cash_account WHERE is_active = 1")
        accounts = cursor.fetchall()
        
        print(f"\n📊 帳戶餘額:")
        total_twd = 0
        total_rmb = 0
        
        for name, currency, balance in accounts:
            print(f"{name} {currency}: {balance:,.2f}")
            if currency == 'TWD':
                total_twd += balance
            elif currency == 'RMB':
                total_rmb += balance
        
        print(f"\n總TWD: {total_twd:,.2f}")
        print(f"總RMB: {total_rmb:,.2f}")
        
        # 檢查買入記錄
        cursor.execute("SELECT twd_cost, rmb_amount FROM purchase_record")
        purchases = cursor.fetchall()
        
        total_twd_spent = sum(p[0] for p in purchases)
        total_rmb_gained = sum(p[1] for p in purchases)
        
        print(f"\n🛒 買入記錄:")
        print(f"總TWD支出: {total_twd_spent:,.2f}")
        print(f"總RMB獲得: {total_rmb_gained:,.2f}")
        
        # 檢查銷售記錄
        cursor.execute("SELECT twd_amount, rmb_amount FROM sales_record")
        sales = cursor.fetchall()
        
        total_twd_gained = sum(s[0] for s in sales)
        total_rmb_sold = sum(s[1] for s in sales)
        
        print(f"\n💰 銷售記錄:")
        print(f"總TWD獲得: {total_twd_gained:,.2f}")
        print(f"總RMB售出: {total_rmb_sold:,.2f}")
        
        # 計算理論餘額
        theoretical_twd = total_twd_gained - total_twd_spent
        theoretical_rmb = total_rmb_gained - total_rmb_sold
        
        print(f"\n🧮 理論餘額:")
        print(f"理論TWD: {theoretical_twd:,.2f}")
        print(f"理論RMB: {theoretical_rmb:,.2f}")
        
        # 差異
        twd_diff = theoretical_twd - total_twd
        rmb_diff = theoretical_rmb - total_rmb
        
        print(f"\n⚠️ 差異:")
        print(f"TWD差異: {twd_diff:,.2f}")
        print(f"RMB差異: {rmb_diff:,.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    simple_debug()
