#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化FIFO表格腳本
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
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
        
        # 創建所有表格
        try:
            print("🔄 開始創建所有表格...")
            db.create_all()
            print("✅ 所有表格創建成功")
        except Exception as e:
            print(f"❌ 創建表格失敗: {e}")
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
        
        # 檢查表格結構
        try:
            # 檢查fifo_inventory表格結構
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(fifo_inventory)"))
                columns = result.fetchall()
                print(f"✅ fifo_inventory表格欄位數量: {len(columns)}")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
                
        except Exception as e:
            print(f"❌ 檢查表格結構失敗: {e}")
        
        print("\n🎯 FIFO表格初始化完成")
        
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 初始化過程中發生錯誤: {e}")
    sys.exit(1)
