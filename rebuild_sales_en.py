#!/usr/bin/env python3
"""
Sales Record Rebuild Tool - Rebuild sales records based on inventory data
Goal: Solve inventory data inconsistency issues and rebuild reasonable sales records
"""

import os
import sqlite3
from datetime import datetime, timedelta

def analyze_inventory_discrepancy():
    """Analyze inventory discrepancy issues"""
    print("Analyzing inventory discrepancy issues...")
    
    try:
        # Connect to current database
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # Check inventory status
        current_cursor.execute("""
            SELECT id, purchase_record_id, rmb_amount, remaining_rmb, 
                   (rmb_amount - remaining_rmb) as allocated_amount,
                   unit_cost_twd, exchange_rate, purchase_date
            FROM fifo_inventory
            ORDER BY purchase_date
        """)
        inventories = current_cursor.fetchall()
        
        print(f"Inventory detailed analysis:")
        total_original = 0
        total_remaining = 0
        total_allocated = 0
        
        for inv in inventories:
            inv_id, purchase_id, rmb_amount, remaining, allocated, unit_cost, exchange_rate, purchase_date = inv
            total_original += rmb_amount
            total_remaining += remaining
            total_allocated += allocated
            
            print(f"   Batch {inv_id}:")
            print(f"     Original amount: ¥{rmb_amount:,.2f}")
            print(f"     Remaining amount: ¥{remaining:,.2f}")
            print(f"     Allocated amount: ¥{allocated:,.2f}")
            print(f"     Unit cost: NT$ {unit_cost:,.2f}")
            print(f"     Exchange rate: {exchange_rate:,.4f}")
            print(f"     Purchase date: {purchase_date}")
            print()
        
        print(f"Summary:")
        print(f"   Total original: ¥{total_original:,.2f}")
        print(f"   Total remaining: ¥{total_remaining:,.2f}")
        print(f"   Total allocated: ¥{total_allocated:,.2f}")
        
        # Analyze inconsistency
        if total_allocated > 0:
            print(f"\nFound inventory inconsistency:")
            print(f"   Inventory shows allocated ¥{total_allocated:,.2f}")
            print(f"   But no corresponding sales records")
            print(f"   This indicates inventory status needs correction")
        
        current_conn.close()
        return inventories, total_allocated
        
    except Exception as e:
        print(f"Failed to analyze inventory discrepancy: {e}")
        return None, 0

def rebuild_sales_records(inventories, total_allocated):
    """Rebuild sales records"""
    print("Starting to rebuild sales records...")
    
    if total_allocated <= 0:
        print("No sales records need to be rebuilt")
        return True
    
    try:
        # Connect to current database
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # 1. Clear existing sales allocation records
        print("   1. Clearing existing sales allocation records...")
        current_cursor.execute("DELETE FROM fifo_sales_allocations")
        
        # 2. Reset inventory remaining amounts
        print("   2. Resetting inventory remaining amounts...")
        current_cursor.execute("""
            UPDATE fifo_inventory 
            SET remaining_rmb = rmb_amount
        """)
        
        # 3. Create virtual sales records to consume allocated inventory
        print("   3. Creating virtual sales records...")
        
        # Get customer list
        current_cursor.execute("SELECT id, name FROM customers WHERE is_active = 1 LIMIT 1")
        customer_result = current_cursor.fetchone()
        if not customer_result:
            print("   No active customers found, cannot create sales records")
            current_conn.close()
            return False
        
        customer_id, customer_name = customer_result
        print(f"   Using customer: {customer_name} (ID: {customer_id})")
        
        # Create sales records for each inventory batch with allocation
        created_sales = []
        created_allocations = []
        
        for inv in inventories:
            inv_id, purchase_id, rmb_amount, remaining, allocated, unit_cost, exchange_rate, purchase_date = inv
            
            if allocated > 0:
                print(f"   Creating sales record for batch {inv_id}: ¥{allocated:,.2f}")
                
                # Create sales record
                sale_date = datetime.fromisoformat(purchase_date) + timedelta(days=1)
                twd_amount = allocated * unit_cost
                
                current_cursor.execute("""
                    INSERT INTO sales_records 
                    (customer_id, rmb_amount, twd_amount, created_at, operator_id, is_settled)
                    VALUES (?, ?, ?, ?, 1, 0)
                """, (customer_id, allocated, twd_amount, sale_date.isoformat()))
                
                sale_id = current_cursor.lastrowid
                created_sales.append(sale_id)
                
                # Create inventory allocation record
                current_cursor.execute("""
                    INSERT INTO fifo_sales_allocations 
                    (fifo_inventory_id, sales_record_id, allocated_rmb, allocated_cost_twd, allocation_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (inv_id, sale_id, allocated, allocated * unit_cost, sale_date.isoformat()))
                
                allocation_id = current_cursor.lastrowid
                created_allocations.append(allocation_id)
                
                # Update inventory remaining amount
                current_cursor.execute("""
                    UPDATE fifo_inventory 
                    SET remaining_rmb = remaining_rmb - ?
                    WHERE id = ?
                """, (allocated, inv_id))
        
        # 4. Commit all changes
        print("   4. Committing changes...")
        current_conn.commit()
        
        print(f"Rebuild completed!")
        print(f"   Created sales records: {len(created_sales)}")
        print(f"   Created allocation records: {len(created_allocations)}")
        
        current_conn.close()
        return True
        
    except Exception as e:
        print(f"Failed to rebuild sales records: {e}")
        if 'current_conn' in locals():
            current_conn.rollback()
            current_conn.close()
        return False

def verify_rebuild():
    """Verify rebuild results"""
    print("Verifying rebuild results...")
    
    try:
        # Connect to current database
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # Check inventory status
        current_cursor.execute("""
            SELECT rmb_amount, remaining_rmb
            FROM fifo_inventory
        """)
        inventories = current_cursor.fetchall()
        
        total_original = sum(inv[0] for inv in inventories)
        total_remaining = sum(inv[1] for inv in inventories)
        total_allocated = total_original - total_remaining
        
        print(f"Inventory status:")
        print(f"   Total batches: {len(inventories)}")
        print(f"   Total original: ¥{total_original:,.2f}")
        print(f"   Total remaining: ¥{total_remaining:,.2f}")
        print(f"   Total allocated: ¥{total_allocated:,.2f}")
        
        # Check sales allocation records
        current_cursor.execute("""
            SELECT allocated_rmb
            FROM fifo_sales_allocations
        """)
        allocations = current_cursor.fetchall()
        total_allocated_sales = sum(alloc[0] for alloc in allocations)
        
        print(f"Sales allocation records:")
        print(f"   Allocation count: {len(allocations)}")
        print(f"   Total allocation amount: ¥{total_allocated_sales:,.2f}")
        
        # Check sales records
        current_cursor.execute("""
            SELECT rmb_amount
            FROM sales_records
        """)
        sales_records = current_cursor.fetchall()
        total_sales = sum(sale[0] for sale in sales_records)
        
        print(f"Sales records:")
        print(f"   Sales record count: {len(sales_records)}")
        print(f"   Total sales amount: ¥{total_sales:,.2f}")
        
        # Check consistency
        if total_allocated == total_allocated_sales and total_allocated_sales == total_sales:
            print("Data consistency check passed!")
            print("   Inventory allocation = Sales allocation = Sales records")
        else:
            print("Data consistency check failed")
            print(f"   Inventory allocation: ¥{total_allocated:,.2f}")
            print(f"   Sales allocation: ¥{total_allocated_sales:,.2f}")
            print(f"   Sales records: ¥{total_sales:,.2f}")
        
        current_conn.close()
        
        return {
            'inventories': len(inventories),
            'total_original': total_original,
            'total_remaining': total_remaining,
            'total_allocated': total_allocated,
            'allocations': len(allocations),
            'total_allocated_sales': total_allocated_sales,
            'sales_records': len(sales_records),
            'total_sales': total_sales
        }
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return None

def main():
    """Main function"""
    print("Sales Record Rebuild Tool")
    print("=" * 50)
    print("Goal: Rebuild sales records based on inventory data to solve data inconsistency issues")
    print("=" * 50)
    
    try:
        # 1. Analyze inventory discrepancy issues
        print("\nStep 1: Analyze inventory discrepancy issues")
        inventories, total_allocated = analyze_inventory_discrepancy()
        
        if inventories is None:
            print("Cannot analyze inventory status, exiting")
            return
        
        # 2. Rebuild sales records
        if total_allocated > 0:
            print("\nStep 2: Rebuild sales records")
            success = rebuild_sales_records(inventories, total_allocated)
            
            if success:
                # 3. Verify results
                print("\nStep 3: Verify rebuild results")
                final_state = verify_rebuild()
                
                if final_state:
                    print("\nSales record rebuild completed successfully!")
                    print("Final status:")
                    print(f"   Inventory batches: {final_state['inventories']}")
                    print(f"   Total original: ¥{final_state['total_original']:,.2f}")
                    print(f"   Total remaining: ¥{final_state['total_remaining']:,.2f}")
                    print(f"   Total allocated: ¥{final_state['total_allocated']:,.2f}")
                    print(f"   Sales records: {final_state['sales_records']}")
                    print(f"   Total sales amount: ¥{final_state['total_sales']:,.2f}")
                    
                    print("\nNext steps:")
                    print("   1. Check inventory management page in web interface")
                    print("   2. Verify inventory data consistency")
                    print("   3. Check cash management and customer receivables")
                    print("   4. Adjust virtual sales records based on actual situation")
                else:
                    print("Verification failed, please check error messages")
            else:
                print("Sales record rebuild failed")
        else:
            print("No inventory inconsistency issues found, no rebuild needed")
            
    except Exception as e:
        print(f"Error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
