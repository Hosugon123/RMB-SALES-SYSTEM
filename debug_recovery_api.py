#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷數據修復 API 問題的腳本
"""

import requests
import json
import time

def test_api_endpoint(url, method="GET", data=None):
    """測試 API 端點"""
    print(f"\n🔍 測試 {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ 不支持的 HTTP 方法: {method}")
            return False
        
        print(f"📊 響應狀態碼: {response.status_code}")
        print(f"📋 響應頭:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"📄 響應內容 (前500字符):")
        content = response.text[:500]
        print(f"  {content}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print("✅ JSON 解析成功")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失敗: {e}")
                return False
        else:
            print(f"❌ HTTP 請求失敗: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 請求超時")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 連接錯誤")
        return False
    except Exception as e:
        print(f"❌ 請求異常: {e}")
        return False

def main():
    """主函數"""
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    print("🚀 開始診斷數據修復 API...")
    print("=" * 60)
    
    # 測試數據狀態 API
    status_url = f"{base_url}/api/admin/data-status"
    status_success = test_api_endpoint(status_url, "GET")
    
    # 測試數據修復 API
    recovery_url = f"{base_url}/api/admin/data-recovery"
    recovery_success = test_api_endpoint(recovery_url, "POST", {})
    
    # 測試管理頁面
    admin_url = f"{base_url}/admin_data_recovery"
    admin_success = test_api_endpoint(admin_url, "GET")
    
    print("\n" + "=" * 60)
    print("📊 診斷結果總結:")
    print(f"  數據狀態 API: {'✅ 成功' if status_success else '❌ 失敗'}")
    print(f"  數據修復 API: {'✅ 成功' if recovery_success else '❌ 失敗'}")
    print(f"  管理頁面: {'✅ 成功' if admin_success else '❌ 失敗'}")
    
    if not any([status_success, recovery_success, admin_success]):
        print("\n⚠️ 所有端點都失敗，可能的原因:")
        print("  1. 應用程序未運行")
        print("  2. 數據庫連接問題")
        print("  3. 代碼語法錯誤")
        print("  4. 依賴模組缺失")
    elif not recovery_success:
        print("\n⚠️ 數據修復 API 失敗，可能的原因:")
        print("  1. 數據庫查詢錯誤")
        print("  2. 模型關係問題")
        print("  3. 數據庫事務問題")
        print("  4. 權限驗證問題")

if __name__ == "__main__":
    main()
