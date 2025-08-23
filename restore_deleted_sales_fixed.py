#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據恢復工具 - 恢復被刪除的售出訂單數據
目標：回到刪除售出訂單之前的完整數據狀態
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db, FIFOInventory, FIFOSalesAllocation, SalesRecord, Customer, CashAccount
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("💡 請確保在正確的目錄中運行此腳本")
    sys.exit(1)

class SalesDataRestorer:
    """售出數據恢復器"""
    
    def __init__(self):
        self.app = app
        self.db = db
        self.session = db.session
        
    def check_database_backup(self):
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
    
    def analyze_current_state(self):
        """分析當前數據狀態"""
        print("🔍 分析當前數據狀態...")
        
        try:
            with self.app.app_context():
                # 檢查庫存狀態
                inventories = FIFOInventory.query.all()
                total_original = sum(inv.rmb_amount for inv in inventories)
                total_remaining = sum(inv.remaining_rmb for inv in inventories)
                total_allocated = sum(inv.rmb_amount - inv.remaining_rmb for inv in inventories)
                
                print(f"📦 庫存狀態:")
                print(f"   總批次: {len(inventories)}")
                print(f"   原始總量: ¥{total_original:,.2f}")
                print(f"   剩餘數量: ¥{total_remaining:,.2f}")
                print(f"   已分配: ¥{total_allocated:,.2f}")
                
                # 檢查銷售分配記錄
                allocations = FIFOSalesAllocation.query.all()
                total_allocated_sales = sum(alloc.allocated_rmb for alloc in allocations)
                
                print(f"📋 銷售分配記錄:")
                print(f"   分配記錄數: {len(allocations)}")
                print(f"   總分配金額: ¥{total_allocated_sales:,.2f}")
                
                # 檢查銷售記錄
                sales_records = SalesRecord.query.all()
                total_sales = sum(sale.rmb_amount for sale in sales_records)
                
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
    
    def restore_from_backup(self, backup_file):
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
                SELECT id, customer_id, rmb_amount, twd_amount, sale_date, description
                FROM sales_records
                ORDER BY sale_date
            """)
            backup_sales = backup_cursor.fetchall()
            
            print(f"📦 備份中找到 {len(backup_sales)} 條銷售記錄")
            
            if not backup_sales:
                print("⚠️ 備份中沒有銷售記錄，無法恢復")
                backup_conn.close()
                return False
            
            # 開始恢復流程
            print("🔄 開始恢復流程...")
            
            with self.app.app_context():
                # 1. 清空現有的銷售分配記錄
                print("   1. 清空現有銷售分配記錄...")
                FIFOSalesAllocation.query.delete()
                
                # 2. 重置庫存剩餘數量
                print("   2. 重置庫存剩餘數量...")
                for inventory in FIFOInventory.query.all():
                    inventory.remaining_rmb = inventory.rmb_amount
                
                # 3. 恢復銷售記錄和分配
                print("   3. 恢復銷售記錄和分配...")
                
                restored_sales = []
                restored_allocations = []
                
                for backup_sale in backup_sales:
                    sale_id, customer_id, rmb_amount, twd_amount, sale_date, description = backup_sale
                    
                    # 檢查銷售記錄是否已存在
                    existing_sale = SalesRecord.query.filter_by(
                        customer_id=customer_id,
                        rmb_amount=rmb_amount,
                        twd_amount=twd_amount,
                        sale_date=datetime.fromisoformat(sale_date)
                    ).first()
                    
                    if not existing_sale:
                        # 創建新的銷售記錄
                        new_sale = SalesRecord(
                            customer_id=customer_id,
                            rmb_amount=rmb_amount,
                            twd_amount=twd_amount,
                            sale_date=datetime.fromisoformat(sale_date),
                            description=description or f"從備份恢復的銷售記錄"
                        )
                        self.session.add(new_sale)
                        restored_sales.append(new_sale)
                        
                        # 為這個銷售記錄分配庫存
                        self._allocate_inventory_for_sale(new_sale, restored_allocations)
                    else:
                        print(f"   ⚠️ 銷售記錄已存在，跳過: {description}")
                
                # 4. 提交所有更改
                print("   4. 提交更改...")
                self.session.commit()
            
            print(f"✅ 恢復完成!")
            print(f"   恢復的銷售記錄: {len(restored_sales)}")
            print(f"   恢復的分配記錄: {len(restored_allocations)}")
            
            backup_conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 從備份恢復失敗: {e}")
            self.session.rollback()
            backup_conn.close()
            return False
    
    def _allocate_inventory_for_sale(self, sale_record, restored_allocations):
        """為銷售記錄分配庫存"""
        rmb_amount = sale_record.rmb_amount
        remaining_to_allocate = rmb_amount
        total_cost = 0
        
        with self.app.app_context():
            # 按買入時間順序獲取有庫存的記錄（FIFO原則）
            available_inventory = (
                FIFOInventory.query
                .filter(FIFOInventory.remaining_rmb > 0)
                .order_by(FIFOInventory.purchase_date.asc())
                .all()
            )
            
            for inventory in available_inventory:
                if remaining_to_allocate <= 0:
                    break
                    
                # 計算本次分配的數量
                allocate_amount = min(remaining_to_allocate, inventory.remaining_rmb)
                
                # 創建分配記錄
                allocation = FIFOSalesAllocation(
                    inventory_id=inventory.id,
                    sales_record_id=sale_record.id,
                    allocated_rmb=allocate_amount,
                    allocated_cost=allocate_amount * inventory.unit_cost_twd,
                    allocation_date=datetime.utcnow()
                )
                
                self.session.add(allocation)
                restored_allocations.append(allocation)
                
                # 更新庫存剩餘數量
                inventory.remaining_rmb -= allocate_amount
                
                # 更新成本
                total_cost += allocate_amount * inventory.unit_cost_twd
                remaining_to_allocate -= allocate_amount
            
            if remaining_to_allocate > 0:
                print(f"   ⚠️ 庫存不足，無法完全分配: 剩餘 ¥{remaining_to_allocate:,.2f}")
    
    def verify_restoration(self):
        """驗證恢復結果"""
        print("🔍 驗證恢復結果...")
        
        try:
            # 重新分析狀態
            current_state = self.analyze_current_state()
            
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
    print("🚀 售出數據恢復工具")
    print("=" * 50)
    print("目標：恢復被刪除的售出訂單數據，回到刪除前的完整狀態")
    print("=" * 50)
    
    # 創建恢復器實例
    restorer = SalesDataRestorer()
    
    try:
        # 1. 檢查當前狀態
        print("\n📊 步驟 1: 分析當前數據狀態")
        current_state = restorer.analyze_current_state()
        
        if not current_state:
            print("❌ 無法分析當前狀態，退出")
            return
        
        # 2. 檢查備份文件
        print("\n📦 步驟 2: 檢查備份文件")
        backup_files = restorer.check_database_backup()
        
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
        success = restorer.restore_from_backup(selected_backup)
        
        if success:
            # 5. 驗證結果
            print("\n✅ 步驟 5: 驗證恢復結果")
            final_state = restorer.verify_restoration()
            
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
