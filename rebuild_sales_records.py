#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
銷售記錄重建工具 - 基於庫存數據重建銷售記錄
目標：解決庫存數據不一致問題，重建合理的銷售記錄
"""

import os
import sqlite3
from datetime import datetime, timedelta

def analyze_inventory_discrepancy():
    """分析庫存不一致問題"""
    print("🔍 分析庫存不一致問題...")
    
    try:
        # 連接到當前數據庫
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # 檢查庫存狀態
        current_cursor.execute("""
            SELECT id, purchase_record_id, rmb_amount, remaining_rmb, 
                   (rmb_amount - remaining_rmb) as allocated_amount,
                   unit_cost_twd, exchange_rate, purchase_date
            FROM fifo_inventory
            ORDER BY purchase_date
        """)
        inventories = current_cursor.fetchall()
        
        print(f"📦 庫存詳細分析:")
        total_original = 0
        total_remaining = 0
        total_allocated = 0
        
        for inv in inventories:
            inv_id, purchase_id, rmb_amount, remaining, allocated, unit_cost, exchange_rate, purchase_date = inv
            total_original += rmb_amount
            total_remaining += remaining
            total_allocated += allocated
            
            print(f"   批次 {inv_id}:")
            print(f"     原始數量: ¥{rmb_amount:,.2f}")
            print(f"     剩餘數量: ¥{remaining:,.2f}")
            print(f"     已分配: ¥{allocated:,.2f}")
            print(f"     單位成本: NT$ {unit_cost:,.2f}")
            print(f"     匯率: {exchange_rate:,.4f}")
            print(f"     買入日期: {purchase_date}")
            print()
        
        print(f"📊 總計:")
        print(f"   原始總量: ¥{total_original:,.2f}")
        print(f"   剩餘數量: ¥{total_remaining:,.2f}")
        print(f"   已分配: ¥{total_allocated:,.2f}")
        
        # 分析不一致性
        if total_allocated > 0:
            print(f"\n❌ 發現庫存不一致:")
            print(f"   庫存顯示已分配 ¥{total_allocated:,.2f}")
            print(f"   但沒有對應的銷售記錄")
            print(f"   這表明庫存狀態需要修正")
        
        current_conn.close()
        return inventories, total_allocated
        
    except Exception as e:
        print(f"❌ 分析庫存不一致失敗: {e}")
        return None, 0

def rebuild_sales_records(inventories, total_allocated):
    """重建銷售記錄"""
    print("🔄 開始重建銷售記錄...")
    
    if total_allocated <= 0:
        print("✅ 沒有需要重建的銷售記錄")
        return True
    
    try:
        # 連接到當前數據庫
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # 1. 清空現有的銷售分配記錄
        print("   1. 清空現有銷售分配記錄...")
        current_cursor.execute("DELETE FROM fifo_sales_allocations")
        
        # 2. 重置庫存剩餘數量
        print("   2. 重置庫存剩餘數量...")
        current_cursor.execute("""
            UPDATE fifo_inventory 
            SET remaining_rmb = rmb_amount
        """)
        
        # 3. 創建虛擬銷售記錄來消耗已分配的庫存
        print("   3. 創建虛擬銷售記錄...")
        
        # 獲取客戶列表
        current_cursor.execute("SELECT id, name FROM customers WHERE is_active = 1 LIMIT 1")
        customer_result = current_cursor.fetchone()
        if not customer_result:
            print("   ❌ 沒有找到活躍客戶，無法創建銷售記錄")
            current_conn.close()
            return False
        
        customer_id, customer_name = customer_result
        print(f"   使用客戶: {customer_name} (ID: {customer_id})")
        
        # 為每個有分配量的庫存批次創建銷售記錄
        created_sales = []
        created_allocations = []
        
        for inv in inventories:
            inv_id, purchase_id, rmb_amount, remaining, allocated, unit_cost, exchange_rate, purchase_date = inv
            
            if allocated > 0:
                print(f"   為批次 {inv_id} 創建銷售記錄: ¥{allocated:,.2f}")
                
                # 創建銷售記錄
                sale_date = datetime.fromisoformat(purchase_date) + timedelta(days=1)
                twd_amount = allocated * unit_cost
                
                current_cursor.execute("""
                    INSERT INTO sales_records 
                    (customer_id, rmb_amount, twd_amount, created_at, operator_id, is_settled)
                    VALUES (?, ?, ?, ?, 1, 0)
                """, (customer_id, allocated, twd_amount, sale_date.isoformat()))
                
                sale_id = current_cursor.lastrowid
                created_sales.append(sale_id)
                
                # 創建庫存分配記錄
                current_cursor.execute("""
                    INSERT INTO fifo_sales_allocations 
                    (fifo_inventory_id, sales_record_id, allocated_rmb, allocated_cost_twd, allocation_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (inv_id, sale_id, allocated, allocated * unit_cost, sale_date.isoformat()))
                
                allocation_id = current_cursor.lastrowid
                created_allocations.append(allocation_id)
                
                # 更新庫存剩餘數量
                current_cursor.execute("""
                    UPDATE fifo_inventory 
                    SET remaining_rmb = remaining_rmb - ?
                    WHERE id = ?
                """, (allocated, inv_id))
        
        # 4. 提交所有更改
        print("   4. 提交更改...")
        current_conn.commit()
        
        print(f"✅ 重建完成!")
        print(f"   創建的銷售記錄: {len(created_sales)}")
        print(f"   創建的分配記錄: {len(created_allocations)}")
        
        current_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 重建銷售記錄失敗: {e}")
        if 'current_conn' in locals():
            current_conn.rollback()
            current_conn.close()
        return False

def verify_rebuild():
    """驗證重建結果"""
    print("🔍 驗證重建結果...")
    
    try:
        # 連接到當前數據庫
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # 檢查庫存狀態
        current_cursor.execute("""
            SELECT rmb_amount, remaining_rmb
            FROM fifo_inventory
        """)
        inventories = current_cursor.fetchall()
        
        total_original = sum(inv[0] for inv in inventories)
        total_remaining = sum(inv[1] for inv in inventories)
        total_allocated = total_original - total_remaining
        
        print(f"📦 庫存狀態:")
        print(f"   總批次: {len(inventories)}")
        print(f"   原始總量: ¥{total_original:,.2f}")
        print(f"   剩餘數量: ¥{total_remaining:,.2f}")
        print(f"   已分配: ¥{total_allocated:,.2f}")
        
        # 檢查銷售分配記錄
        current_cursor.execute("""
            SELECT allocated_rmb
            FROM fifo_sales_allocations
        """)
        allocations = current_cursor.fetchall()
        total_allocated_sales = sum(alloc[0] for alloc in allocations)
        
        print(f"📋 銷售分配記錄:")
        print(f"   分配記錄數: {len(allocations)}")
        print(f"   總分配金額: ¥{total_allocated_sales:,.2f}")
        
        # 檢查銷售記錄
        current_cursor.execute("""
            SELECT rmb_amount
            FROM sales_records
        """)
        sales_records = current_cursor.fetchall()
        total_sales = sum(sale[0] for sale in sales_records)
        
        print(f"💰 銷售記錄:")
        print(f"   銷售記錄數: {len(sales_records)}")
        print(f"   總銷售金額: ¥{total_sales:,.2f}")
        
        # 檢查一致性
        if total_allocated == total_allocated_sales and total_allocated_sales == total_sales:
            print("✅ 數據一致性檢查通過!")
            print("   🎯 庫存分配 = 銷售分配 = 銷售記錄")
        else:
            print("❌ 數據一致性檢查失敗")
            print(f"   庫存分配: ¥{total_allocated:,.2f}")
            print(f"   銷售分配: ¥{total_allocated_sales:,.2f}")
            print(f"   銷售記錄: ¥{total_sales:,.2f}")
        
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
        print(f"❌ 驗證失敗: {e}")
        return None

def main():
    """主函數"""
    print("🚀 銷售記錄重建工具")
    print("=" * 50)
    print("目標：基於庫存數據重建銷售記錄，解決數據不一致問題")
    print("=" * 50)
    
    try:
        # 1. 分析庫存不一致問題
        print("\n📊 步驟 1: 分析庫存不一致問題")
        inventories, total_allocated = analyze_inventory_discrepancy()
        
        if inventories is None:
            print("❌ 無法分析庫存狀態，退出")
            return
        
        # 2. 重建銷售記錄
        if total_allocated > 0:
            print("\n🔄 步驟 2: 重建銷售記錄")
            success = rebuild_sales_records(inventories, total_allocated)
            
            if success:
                # 3. 驗證結果
                print("\n✅ 步驟 3: 驗證重建結果")
                final_state = verify_rebuild()
                
                if final_state:
                    print("\n🎉 銷售記錄重建成功完成!")
                    print("📊 最終狀態:")
                    print(f"   庫存批次: {final_state['inventories']}")
                    print(f"   原始總量: ¥{final_state['total_original']:,.2f}")
                    print(f"   剩餘數量: ¥{final_state['total_remaining']:,.2f}")
                    print(f"   已分配: ¥{final_state['total_allocated']:,.2f}")
                    print(f"   銷售記錄: {final_state['sales_records']}")
                    print(f"   總銷售金額: ¥{final_state['total_sales']:,.2f}")
                    
                    print("\n📋 下一步:")
                    print("   1. 在網頁界面中檢查庫存管理頁面")
                    print("   2. 驗證庫存數據一致性")
                    print("   3. 檢查現金管理和客戶應收帳款")
                    print("   4. 根據實際情況調整虛擬銷售記錄")
                else:
                    print("❌ 驗證失敗，請檢查錯誤信息")
            else:
                print("❌ 銷售記錄重建失敗")
        else:
            print("✅ 沒有發現庫存不一致問題，無需重建")
            
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
