#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIFO功能測試腳本
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db, FIFOService, FIFOInventory, PurchaseRecord, SalesRecord
    print("✅ 成功導入所有必要的模組")
    
    # 創建應用程式上下文
    with app.app_context():
        print("✅ 成功創建應用程式上下文")
        
        # 檢查資料庫連接
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            print("✅ 資料庫連接正常")
        except Exception as e:
            print(f"❌ 資料庫連接失敗: {e}")
            sys.exit(1)
        
        # 檢查FIFO表格是否存在
        try:
            # 檢查fifo_inventory表格
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='fifo_inventory'"))
                if result.fetchone():
                    print("✅ fifo_inventory表格存在")
                else:
                    print("❌ fifo_inventory表格不存在")
                    
                # 檢查fifo_sales_allocations表格
                result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='fifo_sales_allocations'"))
                if result.fetchone():
                    print("✅ fifo_sales_allocations表格存在")
                else:
                    print("❌ fifo_sales_allocations表格不存在")
                
        except Exception as e:
            print(f"❌ 檢查表格失敗: {e}")
        
        # 檢查是否有庫存資料
        try:
            inventory_count = db.session.query(FIFOInventory).count()
            print(f"✅ FIFO庫存記錄數量: {inventory_count}")
            
            if inventory_count > 0:
                # 顯示一些庫存資料
                inventory = db.session.query(FIFOInventory).first()
                print(f"   - 第一筆庫存: ID={inventory.id}, 剩餘RMB={inventory.remaining_rmb}")
                
        except Exception as e:
            print(f"❌ 檢查庫存資料失敗: {e}")
        
        # 檢查是否有買入記錄
        try:
            purchase_count = db.session.query(PurchaseRecord).count()
            print(f"✅ 買入記錄數量: {purchase_count}")
            
        except Exception as e:
            print(f"❌ 檢查買入記錄失敗: {e}")
        
        # 檢查是否有銷售記錄
        try:
            sales_count = db.session.query(SalesRecord).count()
            print(f"✅ 銷售記錄數量: {sales_count}")
            
        except Exception as e:
            print(f"❌ 檢查銷售記錄失敗: {e}")
        
        print("\n🎯 FIFO功能測試完成")
        
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 測試過程中發生錯誤: {e}")
    sys.exit(1)
