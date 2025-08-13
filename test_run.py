#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試運行Flask應用程式
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 開始測試...")

try:
    print("📦 導入應用程式...")
    from app import app
    print("✅ 應用程式導入成功")
    
    print("🔍 檢查應用程式...")
    print(f"   - 類型: {type(app)}")
    print(f"   - 名稱: {app.name}")
    print(f"   - 配置: {app.config.get('ENV', 'production')}")
    
    print("🔍 檢查路由...")
    routes = []
    for rule in app.url_map.iter_rules():
        if 'fifo' in rule.endpoint.lower():
            routes.append(f"{rule.endpoint}: {rule.rule}")
    
    if routes:
        print("✅ FIFO路由:")
        for route in routes:
            print(f"   - {route}")
    else:
        print("❌ 沒有找到FIFO路由")
    
    print("\n🎯 測試完成！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
