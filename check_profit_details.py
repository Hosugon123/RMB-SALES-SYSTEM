#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def check_profit_details():
    db_path = 'instance/sales_system_v4.db'
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=== Profit Details Analysis ===")
        print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Check all sales records
        cursor.execute('''
            SELECT id, customer_id, rmb_amount, twd_amount, created_at 
            FROM sales_records 
            ORDER BY created_at DESC
        ''')
        sales = cursor.fetchall()
        
        print(f"Total sales records: {len(sales)}")
        print("\nAll sales records:")
        for sale in sales:
            print(f'  ID: {sale[0]}, Customer ID: {sale[1]}, RMB: {sale[2]}, TWD: {sale[3]}, Time: {sale[4]}')
        
        # 2. Check FIFO sales allocations
        cursor.execute('''
            SELECT id, sales_record_id, fifo_inventory_id, allocated_rmb, allocated_cost_twd, profit_twd
            FROM fifo_sales_allocations 
            ORDER BY id DESC
        ''')
        allocations = cursor.fetchall()
        
        print(f"\nTotal FIFO allocations: {len(allocations)}")
        print("\nAll FIFO allocations:")
        total_profit_from_allocations = 0
        for alloc in allocations:
            profit = alloc[5] if alloc[5] is not None else 0
            total_profit_from_allocations += profit
            print(f'  ID: {alloc[0]}, Sales ID: {alloc[1]}, FIFO ID: {alloc[2]}, RMB: {alloc[3]}, Cost: {alloc[4]}, Profit: {profit}')
        
        print(f"\nTotal profit from FIFO allocations: {total_profit_from_allocations}")
        
        # 3. Check ledger entries for profit-related records
        cursor.execute('''
            SELECT id, entry_type, amount, description, created_at, profit_before, profit_after, profit_change
            FROM ledger_entries 
            WHERE entry_type IN ('PROFIT_EARNED', 'PROFIT_WITHDRAW')
            ORDER BY created_at DESC
        ''')
        profit_ledger = cursor.fetchall()
        
        print(f"\nProfit-related ledger entries: {len(profit_ledger)}")
        print("\nAll profit ledger entries:")
        total_profit_earned = 0
        total_profit_withdrawn = 0
        for entry in profit_ledger:
            amount = entry[2] if entry[2] is not None else 0
            if entry[1] == 'PROFIT_EARNED':
                total_profit_earned += amount
            elif entry[1] == 'PROFIT_WITHDRAW':
                total_profit_withdrawn += amount
            print(f'  ID: {entry[0]}, Type: {entry[1]}, Amount: {amount}, Desc: {entry[3]}, Time: {entry[4]}')
            if entry[5] is not None:  # profit_before
                print(f'    Profit Before: {entry[5]}, After: {entry[6]}, Change: {entry[7]}')
        
        print(f"\nTotal PROFIT_EARNED: {total_profit_earned}")
        print(f"Total PROFIT_WITHDRAW: {total_profit_withdrawn}")
        print(f"Net profit in ledger: {total_profit_earned - total_profit_withdrawn}")
        
        # 4. Check for missing profit entries
        print(f"\n=== Missing Profit Analysis ===")
        
        # Find sales records that have FIFO allocations but no PROFIT_EARNED entries
        cursor.execute('''
            SELECT DISTINCT fsa.sales_record_id, fsa.profit_twd, fsa.id as allocation_id
            FROM fifo_sales_allocations fsa
            LEFT JOIN ledger_entries le ON le.description LIKE '%' || fsa.sales_record_id || '%' AND le.entry_type = 'PROFIT_EARNED'
            WHERE fsa.profit_twd > 0 AND le.id IS NULL
            ORDER BY fsa.sales_record_id
        ''')
        missing_profit_entries = cursor.fetchall()
        
        print(f"Sales with FIFO allocations but missing PROFIT_EARNED entries: {len(missing_profit_entries)}")
        missing_profit_total = 0
        for entry in missing_profit_entries:
            missing_profit_total += entry[1]
            print(f'  Sales ID: {entry[0]}, Profit: {entry[1]}, Allocation ID: {entry[2]}')
        
        print(f"Total missing profit: {missing_profit_total}")
        
        # 5. Calculate theoretical total profit
        print(f"\n=== Profit Summary ===")
        print(f"Profit from FIFO allocations: {total_profit_from_allocations}")
        print(f"Profit earned in ledger: {total_profit_earned}")
        print(f"Profit withdrawn: {total_profit_withdrawn}")
        print(f"Missing profit entries: {missing_profit_total}")
        print(f"Theoretical total profit: {total_profit_from_allocations}")
        print(f"Actual ledger profit: {total_profit_earned - total_profit_withdrawn}")
        print(f"Difference: {total_profit_from_allocations - (total_profit_earned - total_profit_withdrawn)}")
        
        print(f"\n=== Analysis Complete ===")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_profit_details()
