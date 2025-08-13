#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動Flask應用程式的詳細腳本
"""

import sys
import os
import threading
import time

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_app():
    """啟動應用程式"""
    try:
        print("📦 導入應用程式...")
        from app import app
        
        print("🚀 啟動Flask應用程式...")
        print("📱 請在瀏覽器中訪問: http://localhost:5000")
        print("⏹️  按 Ctrl+C 停止應用程式")
        
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,  # 關閉debug模式避免重載問題
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ 啟動應用程式失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def check_port():
    """檢查端口是否被佔用"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 5000))
            print("✅ 端口5000可用")
            return True
    except OSError:
        print("❌ 端口5000已被佔用")
        return False

if __name__ == "__main__":
    print("🔍 檢查系統...")
    
    # 檢查端口
    if not check_port():
        print("💡 請關閉其他使用端口5000的應用程式")
        sys.exit(1)
    
    # 啟動應用程式
    start_app()

