import sqlite3
import os

def check_rmb_consistency():
    """檢查RMB帳戶餘額和庫存的一致性"""
    
    # 資料庫路徑
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查RMB帳戶餘額和庫存一致性...")
        print("=" * 60)
        
        # 1. 檢查RMB帳戶餘額
        print("\n📊 RMB帳戶餘額:")
        cursor.execute("""
            SELECT id, name, balance, currency 
            FROM cash_accounts 
            WHERE currency = 'RMB' AND is_active = 1
            ORDER BY id
        """)
        accounts = cursor.fetchall()
        
        total_account_balance = 0
        for account in accounts:
            account_id, name, balance, currency = account
            print(f"  ID: {account_id}, 名稱: {name}, 餘額: {balance}, 幣別: {currency}")
            total_account_balance += balance
        
        print(f"\n💰 RMB帳戶總餘額: {total_account_balance}")
        
        # 2. 檢查FIFO庫存
        print("\n📦 FIFO庫存狀態:")
        cursor.execute("""
            SELECT 
                fi.id,
                fi.rmb_amount,
                fi.remaining_rmb,
                fi.unit_cost_twd,
                fi.exchange_rate,
                pr.payment_account_id,
                pr.deposit_account_id,
                pa.name as payment_account_name,
                da.name as deposit_account_name
            FROM fifo_inventory fi
            JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            LEFT JOIN cash_accounts pa ON pr.payment_account_id = pa.id
            LEFT JOIN cash_accounts da ON pr.deposit_account_id = da.id
            ORDER BY fi.id
        """)
        inventory = cursor.fetchall()
        
        total_inventory_rmb = 0
        for inv in inventory:
            inv_id, rmb_amount, remaining_rmb, unit_cost, exchange_rate, payment_account_id, deposit_account_id, payment_account_name, deposit_account_name = inv
            total_inventory_rmb += remaining_rmb
            print(f"  庫存ID: {inv_id}, 原始數量: {rmb_amount}, 剩餘數量: {remaining_rmb}, 單位成本: {unit_cost}, 匯率: {exchange_rate}")
            print(f"    付款帳戶: {payment_account_name or 'N/A'} (ID: {payment_account_id})")
            print(f"    收款帳戶: {deposit_account_name or 'N/A'} (ID: {deposit_account_id})")
        
        print(f"\n📊 FIFO庫存總RMB: {total_inventory_rmb}")
        
        # 3. 檢查差異
        difference = total_inventory_rmb - total_account_balance
        print(f"\n🔍 差異分析:")
        print(f"  庫存RMB: {total_inventory_rmb}")
        print(f"  帳戶餘額: {total_account_balance}")
        print(f"  差異: {difference}")
        
        if abs(difference) > 0.01:  # 允許0.01的浮點數誤差
            print(f"  ❌ 發現不一致！差異: {difference}")
            
            # 4. 檢查是否有銷售分配記錄
            print(f"\n🔍 檢查銷售分配記錄:")
            cursor.execute("""
                SELECT 
                    fsa.id,
                    fsa.fifo_inventory_id,
                    fsa.sales_record_id,
                    fsa.allocated_rmb,
                    fsa.allocated_cost_twd,
                    sr.customer_id,
                    sr.rmb_amount,
                    sr.twd_amount
                FROM fifo_sales_allocations fsa
                JOIN sales_records sr ON fsa.sales_record_id = sr.id
                ORDER BY fsa.id
            """)
            allocations = cursor.fetchall()
            
            if allocations:
                print(f"  找到 {len(allocations)} 筆銷售分配記錄:")
                for alloc in allocations:
                    alloc_id, fifo_inv_id, sales_id, allocated_rmb, allocated_cost, customer_id, rmb_amount, twd_amount = alloc
                    print(f"    分配ID: {alloc_id}, 庫存ID: {fifo_inv_id}, 銷售ID: {sales_id}")
                    print(f"      分配RMB: {allocated_rmb}, 分配成本: {allocated_cost}")
                    print(f"      銷售RMB: {rmb_amount}, 銷售TWD: {twd_amount}")
            else:
                print("  沒有銷售分配記錄")
        else:
            print(f"  ✅ 數據一致！")
        
        # 5. 檢查流水記錄
        print(f"\n📝 檢查RMB相關流水記錄:")
        cursor.execute("""
            SELECT 
                id,
                account_id,
                rmb_change,
                twd_change,
                description,
                created_at
            FROM ledger_entries 
            WHERE rmb_change != 0
            ORDER BY created_at DESC
            LIMIT 10
        """)
        entries = cursor.fetchall()
        
        if entries:
            print(f"  最近10筆RMB流水記錄:")
            for entry in entries:
                entry_id, account_id, rmb_change, twd_change, description, created_at = entry
                print(f"    ID: {entry_id}, 帳戶ID: {account_id}, RMB變動: {rmb_change}, 描述: {description}")
        else:
            print("  沒有RMB流水記錄")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_rmb_consistency()
