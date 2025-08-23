#!/usr/bin/env python3
"""
Simple inventory fix script
"""

import sqlite3

print("Starting inventory fix...")

try:
    # Connect to database
    conn = sqlite3.connect('instance/sales_system_v4.db')
    cursor = conn.cursor()
    
    print("Connected to database")
    
    # Check current inventory
    cursor.execute("SELECT rmb_amount, remaining_rmb FROM fifo_inventory")
    inventories = cursor.fetchall()
    
    print(f"Found {len(inventories)} inventory batches")
    
    total_original = 0
    total_remaining = 0
    
    for inv in inventories:
        rmb_amount, remaining = inv
        total_original += rmb_amount
        total_remaining += remaining
        print(f"Batch: Original ¥{rmb_amount}, Remaining ¥{remaining}")
    
    print(f"Total original: ¥{total_original}")
    print(f"Total remaining: ¥{total_remaining}")
    
    # Fix inventory by setting remaining = original
    cursor.execute("UPDATE fifo_inventory SET remaining_rmb = rmb_amount")
    
    # Clear sales allocations
    cursor.execute("DELETE FROM fifo_sales_allocations")
    
    # Commit changes
    conn.commit()
    
    print("Inventory fixed successfully!")
    
    # Verify fix
    cursor.execute("SELECT rmb_amount, remaining_rmb FROM fifo_inventory")
    inventories_after = cursor.fetchall()
    
    total_remaining_after = sum(inv[1] for inv in inventories_after)
    print(f"Total remaining after fix: ¥{total_remaining_after}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Done")
