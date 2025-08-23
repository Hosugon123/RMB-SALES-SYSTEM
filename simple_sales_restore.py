#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單銷售數據恢復工具 - 直接使用 SQLite 連接
目標：恢復被刪除的售出訂單數據，回到刪除前的完整狀態
"""

import os
import sqlite3
from datetime import datetime

def check_database_backup():
    """檢查是否有數據庫備份"""
    backup_dir = "recovery_backups"
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        if backup_files:
            print(f"📦 找到 {len(backup_files)} 個備份文件:")
            for i, file in enumerate(backup_files, 1):
                file_path = os.path.join(backup_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"   {i}. {file} ({file_size:,} bytes)")
            return backup_files
        else:
            print("❌ 備份目錄中沒有找到 .db 文件")
    else:
        print("❌ 沒有找到 recovery_backups 目錄")
    return []

def analyze_current_state():
    """分析當前數據狀態"""
    print("🔍 分析當前數據狀態...")
    
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
        
        # 分析不一致性
        if total_allocated != total_allocated_sales:
            print(f"❌ 庫存分配與銷售分配不一致:")
            print(f"   庫存已分配: ¥{total_allocated:,.2f}")
            print(f"   銷售分配記錄: ¥{total_allocated_sales:,.2f}")
            print(f"   差異: ¥{abs(total_allocated - total_allocated_sales):,.2f}")
        
        if total_allocated_sales != total_sales:
            print(f"❌ 銷售分配與銷售記錄不一致:")
            print(f"   銷售分配記錄: ¥{total_allocated_sales:,.2f}")
            print(f"   銷售記錄: ¥{total_sales:,.2f}")
            print(f"   差異: ¥{abs(total_allocated_sales - total_sales):,.2f}")
        
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
        print(f"❌ 分析當前狀態失敗: {e}")
        return None

def restore_from_backup(backup_file):
    """從備份文件恢復數據"""
    backup_path = os.path.join("recovery_backups", backup_file)
    
    if not os.path.exists(backup_path):
        print(f"❌ 備份文件不存在: {backup_path}")
        return False
    
    print(f"🔄 從備份文件恢復: {backup_file}")
    
    try:
        # 創建備份數據庫連接
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()
        
        # 獲取備份數據庫中的銷售記錄
        backup_cursor.execute("""
            SELECT id, customer_id, rmb_amount, twd_amount, created_at, description
            FROM sales_records
            ORDER BY created_at
        """)
        backup_sales = backup_cursor.fetchall()
        
        print(f"📦 備份中找到 {len(backup_sales)} 條銷售記錄")
        
        if not backup_sales:
            print("⚠️ 備份中沒有銷售記錄，無法恢復")
            backup_conn.close()
            return False
        
        # 連接到當前數據庫
        current_conn = sqlite3.connect('instance/sales_system_v4.db')
        current_cursor = current_conn.cursor()
        
        # 開始恢復流程
        print("🔄 開始恢復流程...")
        
        # 1. 清空現有的銷售分配記錄
        print("   1. 清空現有銷售分配記錄...")
        current_cursor.execute("DELETE FROM fifo_sales_allocations")
        
        # 2. 重置庫存剩餘數量
        print("   2. 重置庫存剩餘數量...")
        current_cursor.execute("""
            UPDATE fifo_inventory 
            SET remaining_rmb = rmb_amount
        """)
        
        # 3. 恢復銷售記錄和分配
        print("   3. 恢復銷售記錄和分配...")
        
        restored_sales = []
        restored_allocations = []
        
        for backup_sale in backup_sales:
            sale_id, customer_id, rmb_amount, twd_amount, created_at, description = backup_sale
            
            # 檢查銷售記錄是否已存在
            current_cursor.execute("""
                SELECT id FROM sales_records 
                WHERE customer_id = ? AND rmb_amount = ? AND twd_amount = ? AND created_at = ?
            """, (customer_id, rmb_amount, twd_amount, created_at))
            
            existing_sale = current_cursor.fetchone()
            
            if not existing_sale:
                # 創建新的銷售記錄
                current_cursor.execute("""
                    INSERT INTO sales_records (customer_id, rmb_amount, twd_amount, created_at, operator_id)
                    VALUES (?, ?, ?, ?, 1)
                """, (customer_id, rmb_amount, twd_amount, created_at))
                
                new_sale_id = current_cursor.lastrowid
                restored_sales.append(new_sale_id)
                
                # 為這個銷售記錄分配庫存
                allocate_inventory_for_sale(current_cursor, new_sale_id, rmb_amount, restored_allocations)
            else:
                print(f"   ⚠️ 銷售記錄已存在，跳過: {description}")
        
        # 4. 提交所有更改
        print("   4. 提交更改...")
        current_conn.commit()
        
        print(f"✅ 恢復完成!")
        print(f"   恢復的銷售記錄: {len(restored_sales)}")
        print(f"   恢復的分配記錄: {len(restored_allocations)}")
        
        backup_conn.close()
        current_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 從備份恢復失敗: {e}")
        if 'current_conn' in locals():
            current_conn.rollback()
            current_conn.close()
        if 'backup_conn' in locals():
            backup_conn.close()
        return False

def allocate_inventory_for_sale(cursor, sale_id, rmb_amount, restored_allocations):
    """為銷售記錄分配庫存"""
    remaining_to_allocate = rmb_amount
    
    # 按買入時間順序獲取有庫存的記錄（FIFO原則）
    cursor.execute("""
        SELECT id, remaining_rmb, unit_cost_twd
        FROM fifo_inventory
        WHERE remaining_rmb > 0
        ORDER BY purchase_date ASC
    """)
    available_inventory = cursor.fetchall()
    
    for inventory in available_inventory:
        if remaining_to_allocate <= 0:
            break
            
        inventory_id, remaining_rmb, unit_cost_twd = inventory
        
        # 計算本次分配的數量
        allocate_amount = min(remaining_to_allocate, remaining_rmb)
        
        # 創建分配記錄
        cursor.execute("""
            INSERT INTO fifo_sales_allocations 
            (fifo_inventory_id, sales_record_id, allocated_rmb, allocated_cost_twd, allocation_date)
            VALUES (?, ?, ?, ?, ?)
        """, (inventory_id, sale_id, allocate_amount, allocate_amount * unit_cost_twd, datetime.utcnow().isoformat()))
        
        restored_allocations.append(cursor.lastrowid)
        
        # 更新庫存剩餘數量
        cursor.execute("""
            UPDATE fifo_inventory 
            SET remaining_rmb = remaining_rmb - ?
            WHERE id = ?
        """, (allocate_amount, inventory_id))
        
        remaining_to_allocate -= allocate_amount
    
    if remaining_to_allocate > 0:
        print(f"   ⚠️ 庫存不足，無法完全分配: 剩餘 ¥{remaining_to_allocate:,.2f}")

def verify_restoration():
    """驗證恢復結果"""
    print("🔍 驗證恢復結果...")
    
    try:
        # 重新分析狀態
        current_state = analyze_current_state()
        
        if current_state:
            # 檢查一致性
            if (current_state['total_allocated'] == current_state['total_allocated_sales'] and 
                current_state['total_allocated_sales'] == current_state['total_sales']):
                print("✅ 數據一致性檢查通過!")
                print("   🎯 庫存分配 = 銷售分配 = 銷售記錄")
            else:
                print("❌ 數據一致性檢查失敗")
                print("   請檢查恢復過程中的錯誤")
        
        return current_state
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return None

def main():
    """主函數"""
    print("🚀 簡單售出數據恢復工具")
    print("=" * 50)
    print("目標：恢復被刪除的售出訂單數據，回到刪除前的完整狀態")
    print("=" * 50)
    
    try:
        # 1. 檢查當前狀態
        print("\n📊 步驟 1: 分析當前數據狀態")
        current_state = analyze_current_state()
        
        if not current_state:
            print("❌ 無法分析當前狀態，退出")
            return
        
        # 2. 檢查備份文件
        print("\n📦 步驟 2: 檢查備份文件")
        backup_files = check_database_backup()
        
        if not backup_files:
            print("❌ 沒有找到備份文件，無法恢復")
            print("💡 請先創建數據庫備份")
            return
        
        # 3. 選擇備份文件
        print("\n🎯 步驟 3: 選擇要恢復的備份文件")
        print("建議選擇刪除售出訂單之前的備份文件")
        
        # 自動選擇最新的備份文件
        selected_backup = backup_files[0]  # 選擇第一個備份文件
        print(f"自動選擇: {selected_backup}")
        
        # 4. 執行恢復
        print("\n🔄 步驟 4: 執行數據恢復")
        success = restore_from_backup(selected_backup)
        
        if success:
            # 5. 驗證結果
            print("\n✅ 步驟 5: 驗證恢復結果")
            final_state = verify_restoration()
            
            if final_state:
                print("\n🎉 數據恢復成功完成!")
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
            else:
                print("❌ 驗證失敗，請檢查錯誤信息")
        else:
            print("❌ 數據恢復失敗")
            
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
