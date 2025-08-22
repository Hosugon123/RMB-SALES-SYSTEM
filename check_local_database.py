import sqlite3
import os
from datetime import datetime

def check_local_database():
    """檢查本地資料庫的完整狀態，作為參考基準"""
    
    # 資料庫路徑
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查本地資料庫完整狀態...")
        print("=" * 60)
        print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"資料庫路徑: {db_path}")
        
        # 1. 檢查資料庫基本信息
        print("\n📊 資料庫基本信息:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"  總表數: {len(tables)}")
        for table in tables:
            print(f"    - {table[0]}")
        
        # 2. 檢查RMB帳戶餘額
        print("\n💰 RMB帳戶餘額:")
        cursor.execute("""
            SELECT id, name, balance, currency, holder_id, is_active
            FROM cash_accounts 
            WHERE currency = 'RMB' AND is_active = 1
            ORDER BY id
        """)
        accounts = cursor.fetchall()
        
        total_account_balance = 0
        for account in accounts:
            account_id, name, balance, currency, holder_id, is_active = account
            print(f"  ID: {account_id}, 名稱: {name}, 餘額: {balance}, 持有人ID: {holder_id}")
            total_account_balance += balance
        
        print(f"\n💰 RMB帳戶總餘額: {total_account_balance}")
        
        # 3. 檢查FIFO庫存
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
                da.name as deposit_account_name,
                pr.purchase_date
            FROM fifo_inventory fi
            JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            LEFT JOIN cash_accounts pa ON pr.payment_account_id = pa.id
            LEFT JOIN cash_accounts da ON pr.deposit_account_id = da.id
            ORDER BY fi.id
        """)
        inventory = cursor.fetchall()
        
        total_inventory_rmb = 0
        for inv in inventory:
            inv_id, rmb_amount, remaining_rmb, unit_cost, exchange_rate, payment_account_id, deposit_account_id, payment_account_name, deposit_account_name, purchase_date = inv
            total_inventory_rmb += remaining_rmb
            print(f"  庫存ID: {inv_id}, 原始數量: {rmb_amount}, 剩餘數量: {remaining_rmb}")
            print(f"    單位成本: {unit_cost}, 匯率: {exchange_rate}")
            print(f"    付款帳戶: {payment_account_name or 'N/A'} (ID: {payment_account_id})")
            print(f"    收款帳戶: {deposit_account_name or 'N/A'} (ID: {deposit_account_id})")
            print(f"    買入日期: {purchase_date}")
        
        print(f"\n📊 FIFO庫存總RMB: {total_inventory_rmb}")
        
        # 4. 檢查差異
        difference = total_inventory_rmb - total_account_balance
        print(f"\n🔍 差異分析:")
        print(f"  庫存RMB: {total_inventory_rmb}")
        print(f"  帳戶餘額: {total_account_balance}")
        print(f"  差異: {difference}")
        
        if abs(difference) > 0.01:
            print(f"  ❌ 發現不一致！差異: {difference}")
        else:
            print(f"  ✅ 數據一致！")
        
        # 5. 檢查銷售分配記錄
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
                sr.twd_amount,
                sr.status
            FROM fifo_sales_allocations fsa
            JOIN sales_records sr ON fsa.sales_record_id = sr.id
            ORDER BY fsa.id
        """)
        allocations = cursor.fetchall()
        
        if allocations:
            print(f"  找到 {len(allocations)} 筆銷售分配記錄:")
            for alloc in allocations:
                alloc_id, fifo_inv_id, sales_id, allocated_rmb, allocated_cost, customer_id, rmb_amount, twd_amount, status = alloc
                print(f"    分配ID: {alloc_id}, 庫存ID: {fifo_inv_id}, 銷售ID: {sales_id}")
                print(f"      分配RMB: {allocated_rmb}, 分配成本: {allocated_cost}")
                print(f"      銷售RMB: {rmb_amount}, 銷售TWD: {twd_amount}, 狀態: {status}")
        else:
            print("  沒有銷售分配記錄")
        
        # 6. 檢查流水記錄
        print(f"\n📝 檢查最近流水記錄:")
        cursor.execute("""
            SELECT 
                id,
                account_id,
                rmb_change,
                twd_change,
                description,
                entry_type,
                entry_date
            FROM ledger_entries 
            ORDER BY entry_date DESC
            LIMIT 10
        """)
        entries = cursor.fetchall()
        
        if entries:
            print(f"  最近10筆流水記錄:")
            for entry in entries:
                entry_id, account_id, rmb_change, twd_change, description, entry_type, entry_date = entry
                print(f"    ID: {entry_id}, 帳戶ID: {account_id}, RMB變動: {rmb_change}, TWD變動: {twd_change}")
                print(f"      類型: {entry_type}, 描述: {description}, 日期: {entry_date}")
        else:
            print("  沒有流水記錄")
        
        # 7. 檢查持有人和帳戶
        print(f"\n👥 檢查持有人和帳戶:")
        cursor.execute("""
            SELECT 
                h.id,
                h.name as holder_name,
                COUNT(ca.id) as account_count,
                SUM(CASE WHEN ca.currency = 'TWD' THEN ca.balance ELSE 0 END) as total_twd,
                SUM(CASE WHEN ca.currency = 'RMB' THEN ca.balance ELSE 0 END) as total_rmb
            FROM holders h
            LEFT JOIN cash_accounts ca ON h.id = ca.holder_id AND ca.is_active = 1
            WHERE h.is_active = 1
            GROUP BY h.id, h.name
            ORDER BY h.id
        """)
        holders = cursor.fetchall()
        
        for holder in holders:
            holder_id, holder_name, account_count, total_twd, total_rmb = holder
            print(f"  持有人 {holder_id}: {holder_name}")
            print(f"    帳戶數量: {account_count}, TWD總額: {total_twd or 0}, RMB總額: {total_rmb or 0}")
        
        # 8. 生成資料庫摘要報告
        print(f"\n📋 資料庫摘要報告:")
        print(f"  - 總表數: {len(tables)}")
        print(f"  - RMB帳戶數: {len(accounts)}")
        print(f"  - FIFO庫存批次: {len(inventory)}")
        print(f"  - 銷售分配記錄: {len(allocations)}")
        print(f"  - 流水記錄: {len(entries)} (顯示最近10筆)")
        print(f"  - 持有人數: {len(holders)}")
        print(f"  - RMB庫存總額: {total_inventory_rmb}")
        print(f"  - RMB帳戶總餘額: {total_account_balance}")
        print(f"  - 數據一致性: {'✅ 一致' if abs(difference) <= 0.01 else '❌ 不一致'}")
        
        conn.close()
        
        # 9. 保存檢查結果到文件
        save_report_to_file(db_path, tables, accounts, inventory, allocations, entries, holders, total_inventory_rmb, total_account_balance, difference)
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

def save_report_to_file(db_path, tables, accounts, inventory, allocations, entries, holders, total_inventory_rmb, total_account_balance, difference):
    """保存檢查結果到文件"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'database_status_report_{timestamp}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("資料庫狀態檢查報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"資料庫路徑: {db_path}\n\n")
            
            f.write("📊 資料庫基本信息:\n")
            f.write(f"  總表數: {len(tables)}\n")
            for table in tables:
                f.write(f"    - {table[0]}\n")
            
            f.write(f"\n💰 RMB帳戶總餘額: {total_account_balance}\n")
            f.write(f"📦 FIFO庫存總RMB: {total_inventory_rmb}\n")
            f.write(f"🔍 差異: {difference}\n")
            f.write(f"📋 數據一致性: {'✅ 一致' if abs(difference) <= 0.01 else '❌ 不一致'}\n")
        
        print(f"\n📄 檢查報告已保存到: {report_file}")
        
    except Exception as e:
        print(f"⚠️  保存報告失敗: {e}")

if __name__ == "__main__":
    check_local_database()
