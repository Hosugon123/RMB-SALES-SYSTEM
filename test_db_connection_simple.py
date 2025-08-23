#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的資料庫連接測試
"""

import requests
import json

def test_simple_endpoint():
    """測試簡單的端點"""
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 測試根路徑
    try:
        print("🔍 測試根路徑...")
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print("✅ 根路徑正常")
        else:
            print(f"⚠️  根路徑異常: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ 測試根路徑失敗: {e}")
    
    print("-" * 40)
    
    # 測試登入頁面
    try:
        print("🔍 測試登入頁面...")
        response = requests.get(f"{base_url}/login", timeout=10)
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print("✅ 登入頁面正常")
        else:
            print(f"⚠️  登入頁面異常: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ 測試登入頁面失敗: {e}")
    
    print("-" * 40)
    
    # 測試數據修復頁面
    try:
        print("🔍 測試數據修復頁面...")
        response = requests.get(f"{base_url}/admin_data_recovery", timeout=10)
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print("✅ 數據修復頁面正常")
        else:
            print(f"⚠️  數據修復頁面異常: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ 測試數據修復頁面失敗: {e}")

if __name__ == "__main__":
    test_simple_endpoint()
