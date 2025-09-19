#!/usr/bin/env python3
"""
Render 環境測試腳本
用於驗證 Render Cron Job 環境是否正常
"""

import os
import sys
import datetime

def test_environment():
    """測試環境變數和依賴"""
    print("🔍 測試 Render 環境...")
    print(f"Python 版本: {sys.version}")
    print(f"當前時間: {datetime.datetime.now()}")
    
    # 檢查環境變數
    env_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GCS_BUCKET_NAME', 
        'TARGET_URL'
    ]
    
    print("\n📋 環境變數檢查:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:50]}..." if len(value) > 50 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定")
    
    # 測試依賴套件
    print("\n📦 依賴套件檢查:")
    packages = [
        'pandas',
        'openpyxl', 
        'selenium',
        'webdriver_manager',
        'google.cloud.storage'
    ]
    
    for package in packages:
        try:
            if package == 'google.cloud.storage':
                from google.cloud import storage
                print(f"✅ {package}: 可用")
            elif package == 'webdriver_manager':
                import webdriver_manager
                print(f"✅ {package}: 可用")
            else:
                __import__(package)
                print(f"✅ {package}: 可用")
        except ImportError as e:
            print(f"❌ {package}: 不可用 - {e}")
    
    print("\n🎯 測試完成！")

if __name__ == "__main__":
    test_environment()
