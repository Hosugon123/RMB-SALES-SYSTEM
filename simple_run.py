#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最簡單的啟動腳本
"""

try:
    from app import app
    print("✅ 應用程式導入成功")
    
    if __name__ == "__main__":
        print("🚀 啟動應用程式...")
        app.run(debug=True, port=5000)
        
except Exception as e:
    print(f"❌ 啟動失敗: {e}")
    import traceback
    traceback.print_exc()

