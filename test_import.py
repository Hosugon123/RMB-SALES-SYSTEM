#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試應用程式導入
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 開始測試導入...")

try:
    print("📦 導入Flask...")
    from flask import Flask
    print("✅ Flask導入成功")
except Exception as e:
    print(f"❌ Flask導入失敗: {e}")
    sys.exit(1)

try:
    print("📦 導入SQLAlchemy...")
    from flask_sqlalchemy import SQLAlchemy
    print("✅ SQLAlchemy導入成功")
except Exception as e:
    print(f"❌ SQLAlchemy導入失敗: {e}")
    sys.exit(1)

try:
    print("📦 導入應用程式...")
    from app import app
    print("✅ 應用程式導入成功")
except Exception as e:
    print(f"❌ 應用程式導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("📦 檢查應用程式類型...")
    print(f"✅ 應用程式類型: {type(app)}")
    print(f"✅ 應用程式名稱: {app.name}")
except Exception as e:
    print(f"❌ 檢查應用程式失敗: {e}")
    sys.exit(1)

print("\n🎉 所有導入測試都通過了！")

