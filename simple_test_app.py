#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的應用程序測試腳本
"""

try:
    print("🔍 嘗試導入應用程序...")
    from app import app
    print("✅ 應用程序導入成功")
    
    print("🔍 檢查應用程序配置...")
    print(f"   - 應用程序名稱: {app.name}")
    print(f"   - 調試模式: {app.debug}")
    print(f"   - 數據庫 URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
    
    print("🔍 檢查路由...")
    routes = []
    for rule in app.url_map.iter_rules():
        if 'admin' in rule.rule or 'data' in rule.rule:
            routes.append(rule.rule)
    
    print(f"   - 找到 {len(routes)} 個相關路由:")
    for route in routes:
        print(f"     * {route}")
    
    print("\n🎉 應用程序檢查完成！")
    
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
except Exception as e:
    print(f"❌ 其他錯誤: {e}")
    import traceback
    traceback.print_exc()
