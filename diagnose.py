#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷腳本 - 檢查FIFO功能的所有問題
"""

import sys
import os
import traceback

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """檢查所有必要的模組導入"""
    print("🔍 檢查模組導入...")
    
    try:
        from app import app
        print("✅ Flask應用程式導入成功")
    except Exception as e:
        print(f"❌ Flask應用程式導入失敗: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app import db
        print("✅ 資料庫導入成功")
    except Exception as e:
        print(f"❌ 資料庫導入失敗: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app import FIFOService
        print("✅ FIFOService導入成功")
    except Exception as e:
        print(f"❌ FIFOService導入失敗: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app import FIFOInventory
        print("✅ FIFOInventory模型導入成功")
    except Exception as e:
        print(f"❌ FIFOInventory模型導入失敗: {e}")
        traceback.print_exc()
        return False
    
    return True

def check_database():
    """檢查資料庫連接和表格"""
    print("\n🔍 檢查資料庫...")
    
    try:
        from app import app, db
        
        with app.app_context():
            # 檢查資料庫連接
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("SELECT 1"))
                print("✅ 資料庫連接正常")
            except Exception as e:
                print(f"❌ 資料庫連接失敗: {e}")
                return False
            
            # 檢查表格
            try:
                with db.engine.connect() as conn:
                    # 檢查fifo_inventory表格
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
                return False
                
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        traceback.print_exc()
        return False
    
    return True

def check_routes():
    """檢查路由是否正確定義"""
    print("\n🔍 檢查路由...")
    
    try:
        from app import app
        
        # 檢查FIFO相關路由
        routes = []
        for rule in app.url_map.iter_rules():
            if 'fifo' in rule.endpoint.lower():
                routes.append(rule.endpoint)
        
        if routes:
            print(f"✅ 找到FIFO相關路由: {routes}")
        else:
            print("❌ 沒有找到FIFO相關路由")
            return False
            
    except Exception as e:
        print(f"❌ 路由檢查失敗: {e}")
        traceback.print_exc()
        return False
    
    return True

def check_templates():
    """檢查模板文件是否存在"""
    print("\n🔍 檢查模板...")
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'fifo_inventory.html')
    
    if os.path.exists(template_path):
        print(f"✅ FIFO庫存模板存在: {template_path}")
    else:
        print(f"❌ FIFO庫存模板不存在: {template_path}")
        return False
    
    return True

def main():
    """主函數"""
    print("🚀 開始診斷FIFO功能...\n")
    
    all_passed = True
    
    # 檢查導入
    if not check_imports():
        all_passed = False
    
    # 檢查資料庫
    if not check_database():
        all_passed = False
    
    # 檢查路由
    if not check_routes():
        all_passed = False
    
    # 檢查模板
    if not check_templates():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有檢查都通過了！FIFO功能應該可以正常運行。")
        print("💡 建議：嘗試訪問 http://localhost:5000/fifo-inventory")
    else:
        print("❌ 發現了一些問題，請根據上面的錯誤信息進行修復。")
    print("="*50)

if __name__ == "__main__":
    main()

