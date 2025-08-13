#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復FIFO庫存記錄問題的腳本
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_existing_data():
    """檢查現有的資料"""
    print("🔍 檢查現有資料...")
    
    try:
        from app import app, db, PurchaseRecord, FIFOInventory, SalesRecord
        
        with app.app_context():
            # 檢查買入記錄
            purchase_count = db.session.query(PurchaseRecord).count()
            print(f"✅ 買入記錄數量: {purchase_count}")
            
            if purchase_count > 0:
                purchases = db.session.query(PurchaseRecord).all()
                print("📋 買入記錄詳情:")
                for purchase in purchases:
                    print(f"   - ID: {purchase.id}, RMB: {purchase.rmb_amount}, 匯率: {purchase.exchange_rate}, 日期: {purchase.purchase_date}")
            
            # 檢查FIFO庫存記錄
            inventory_count = db.session.query(FIFOInventory).count()
            print(f"✅ FIFO庫存記錄數量: {inventory_count}")
            
            # 檢查銷售記錄
            sales_count = db.session.query(SalesRecord).count()
            print(f"✅ 銷售記錄數量: {sales_count}")
            
            return purchase_count, inventory_count, sales_count
            
    except Exception as e:
        print(f"❌ 檢查資料失敗: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

def create_missing_fifo_records():
    """為現有的買入記錄創建缺失的FIFO庫存記錄"""
    print("\n🔧 創建缺失的FIFO庫存記錄...")
    
    try:
        from app import app, db, PurchaseRecord, FIFOService
        
        with app.app_context():
            # 獲取所有買入記錄
            purchases = db.session.query(PurchaseRecord).all()
            
            if not purchases:
                print("❌ 沒有找到買入記錄")
                return 0
            
            created_count = 0
            
            for purchase in purchases:
                try:
                    # 檢查是否已經有對應的FIFO庫存記錄
                    existing_inventory = db.session.query(FIFOInventory).filter_by(purchase_record_id=purchase.id).first()
                    
                    if existing_inventory:
                        print(f"✅ 買入記錄 {purchase.id} 已有FIFO庫存記錄")
                        continue
                    
                    # 創建FIFO庫存記錄
                    print(f"🔄 為買入記錄 {purchase.id} 創建FIFO庫存記錄...")
                    FIFOService.create_inventory_from_purchase(purchase)
                    created_count += 1
                    print(f"✅ 成功創建FIFO庫存記錄")
                    
                except Exception as e:
                    print(f"❌ 為買入記錄 {purchase.id} 創建FIFO庫存記錄失敗: {e}")
                    continue
            
            print(f"🎯 總共創建了 {created_count} 個FIFO庫存記錄")
            return created_count
            
    except Exception as e:
        print(f"❌ 創建FIFO庫存記錄失敗: {e}")
        import traceback
        traceback.print_exc()
        return 0

def verify_fifo_data():
    """驗證FIFO資料是否正確"""
    print("\n🔍 驗證FIFO資料...")
    
    try:
        from app import app, db, FIFOInventory, PurchaseRecord
        
        with app.app_context():
            # 檢查FIFO庫存記錄
            inventory_records = db.session.query(FIFOInventory).all()
            
            if not inventory_records:
                print("❌ 沒有FIFO庫存記錄")
                return False
            
            print(f"✅ 找到 {len(inventory_records)} 個FIFO庫存記錄:")
            
            for inventory in inventory_records:
                purchase = db.session.get(PurchaseRecord, inventory.purchase_record_id)
                if purchase:
                    print(f"   - 庫存ID: {inventory.id}, 買入ID: {purchase.id}, RMB: {inventory.rmb_amount}, 剩餘: {inventory.remaining_rmb}")
                else:
                    print(f"   - 庫存ID: {inventory.id}, 買入記錄不存在!")
            
            return True
            
    except Exception as e:
        print(f"❌ 驗證FIFO資料失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始修復FIFO庫存記錄問題...\n")
    
    # 檢查現有資料
    purchase_count, inventory_count, sales_count = check_existing_data()
    
    if purchase_count == 0:
        print("❌ 沒有買入記錄，無法創建FIFO庫存")
        return
    
    if inventory_count == 0:
        print("⚠️  沒有FIFO庫存記錄，需要創建")
        # 創建缺失的FIFO庫存記錄
        created_count = create_missing_fifo_records()
        
        if created_count > 0:
            print("✅ FIFO庫存記錄創建完成")
            # 驗證資料
            verify_fifo_data()
        else:
            print("❌ FIFO庫存記錄創建失敗")
    else:
        print("✅ 已有FIFO庫存記錄")
        # 驗證資料
        verify_fifo_data()
    
    print("\n🎯 修復完成！")

if __name__ == "__main__":
    main()

