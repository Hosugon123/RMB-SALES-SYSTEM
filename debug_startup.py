#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試啟動問題的腳本
"""

import sys
import os
import traceback

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """測試導入"""
    print("🔍 測試導入...")
    
    try:
        from app import app
        print("✅ 應用程式導入成功")
        return app
    except Exception as e:
        print(f"❌ 應用程式導入失敗: {e}")
        traceback.print_exc()
        return None

def test_app_context(app):
    """測試應用程式上下文"""
    print("\n🔍 測試應用程式上下文...")
    
    try:
        with app.app_context():
            print("✅ 應用程式上下文創建成功")
            return True
    except Exception as e:
        print(f"❌ 應用程式上下文創建失敗: {e}")
        traceback.print_exc()
        return False

def test_database(app):
    """測試資料庫"""
    print("\n🔍 測試資料庫...")
    
    try:
        from app import db
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            print("✅ 資料庫連接成功")
            return True
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        traceback.print_exc()
        return False

def test_routes(app):
    """測試路由"""
    print("\n🔍 測試路由...")
    
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            if 'fifo' in rule.endpoint.lower():
                routes.append(f"{rule.endpoint}: {rule.rule}")
        
        if routes:
            print("✅ FIFO路由:")
            for route in routes:
                print(f"   - {route}")
            return True
        else:
            print("❌ 沒有找到FIFO路由")
            return False
    except Exception as e:
        print(f"❌ 路由檢查失敗: {e}")
        traceback.print_exc()
        return False

def test_run(app):
    """測試運行"""
    print("\n🔍 測試運行...")
    
    try:
        print("🚀 嘗試啟動應用程式...")
        print("📱 請在瀏覽器中訪問: http://localhost:5000")
        print("⏹️  按 Ctrl+C 停止應用程式")
        
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始調試啟動問題...\n")
    
    # 測試導入
    app = test_import()
    if not app:
        print("❌ 導入失敗，無法繼續")
        return
    
    # 測試應用程式上下文
    if not test_app_context(app):
        print("❌ 應用程式上下文測試失敗")
        return
    
    # 測試資料庫
    if not test_database(app):
        print("❌ 資料庫測試失敗")
        return
    
    # 測試路由
    if not test_routes(app):
        print("❌ 路由測試失敗")
        return
    
    print("\n🎉 所有測試都通過了！")
    
    # 嘗試啟動
    test_run(app)

if __name__ == "__main__":
    main()

