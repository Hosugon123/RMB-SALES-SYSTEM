#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復 API 的腳本
"""

import requests
import json
import time

def test_data_status_api():
    """測試數據狀態 API"""
    try:
        print("🔍 測試數據狀態 API...")
        response = requests.get("http://localhost:5000/api/admin/data-status")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 數據狀態 API 測試成功！")
            print(f"📊 響應數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 數據狀態 API 測試失敗: {response.status_code}")
            print(f"錯誤信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到應用程序，請確保應用程序正在運行")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_data_recovery_api():
    """測試數據修復 API"""
    try:
        print("\n🔧 測試數據修復 API...")
        response = requests.post("http://localhost:5000/api/admin/data-recovery")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 數據修復 API 測試成功！")
            print(f"📊 響應數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 數據修復 API 測試失敗: {response.status_code}")
            print(f"錯誤信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到應用程序，請確保應用程序正在運行")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_admin_page():
    """測試管理頁面"""
    try:
        print("\n🌐 測試管理頁面...")
        response = requests.get("http://localhost:5000/admin_data_recovery")
        
        if response.status_code == 200:
            print("✅ 管理頁面測試成功！")
            print(f"📄 頁面大小: {len(response.text)} 字符")
            return True
        else:
            print(f"❌ 管理頁面測試失敗: {response.status_code}")
            print(f"錯誤信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到應用程序，請確保應用程序正在運行")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試修復 API...")
    print("="*50)
    
    # 等待應用程序啟動
    print("⏳ 等待應用程序啟動...")
    time.sleep(3)
    
    # 測試所有 API
    status_success = test_data_status_api()
    recovery_success = test_data_recovery_api()
    page_success = test_admin_page()
    
    print("\n" + "="*50)
    print("📊 測試結果總結:")
    print(f"   - 數據狀態 API: {'✅ 成功' if status_success else '❌ 失敗'}")
    print(f"   - 數據修復 API: {'✅ 成功' if recovery_success else '❌ 失敗'}")
    print(f"   - 管理頁面: {'✅ 成功' if page_success else '❌ 失敗'}")
    
    if all([status_success, recovery_success, page_success]):
        print("\n🎉 所有測試都通過了！修復 API 已準備就緒。")
        print("\n📱 您現在可以:")
        print("   1. 訪問 http://localhost:5000/admin_data_recovery")
        print("   2. 檢查當前數據狀態")
        print("   3. 執行數據修復")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息。")

if __name__ == "__main__":
    main()
