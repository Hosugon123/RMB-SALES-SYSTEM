#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試腳本 - 診斷導入問題
"""

print("🚀 腳本開始執行...")

try:
    print("1. 導入基本模組...")
    import sys
    import os
    print(f"   ✅ 當前目錄: {os.getcwd()}")
    print(f"   ✅ Python路徑: {sys.path[0]}")
    
    print("2. 嘗試導入Flask應用...")
    from app import app
    print("   ✅ Flask應用導入成功")
    
    print("3. 嘗試導入數據庫...")
    from app import db
    print("   ✅ 數據庫導入成功")
    
    print("4. 嘗試導入模型...")
    from models import User
    print("   ✅ 模型導入成功")
    
    print("✅ 所有導入都成功！")
    
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()

print("🏁 腳本執行完成")
