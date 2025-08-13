#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動Flask應用程式腳本
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✅ 成功導入Flask應用程式")
    
    if __name__ == '__main__':
        print("🚀 啟動Flask應用程式...")
        print("📱 請在瀏覽器中訪問: http://localhost:5000")
        print("⏹️  按 Ctrl+C 停止應用程式")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 啟動應用程式失敗: {e}")
    sys.exit(1)

