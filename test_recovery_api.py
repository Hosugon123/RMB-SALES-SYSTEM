#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據修復 API 的診斷腳本
"""

import requests
import json

def test_data_status_api():
    """測試數據狀態 API"""
    print("🔍 測試數據狀態 API...")
    
    try:
        response = requests.get('https://rmb-sales-system-test1.onrender.com/api/admin/data-status')
        print(f"狀態碼: {response.status_code}")
        print(f"響應頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ JSON 響應成功:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失敗: {e}")
                print(f"響應內容: {response.text[:500]}")
        else:
            print(f"❌ API 請求失敗: {response.status_code}")
            print(f"響應內容: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 請求異常: {e}")

def test_data_recovery_api():
    """測試數據修復 API"""
    print("\n🔧 測試數據修復 API...")
    
    try:
        response = requests.post('https://rmb-sales-system-test1.onrender.com/api/admin/data-recovery')
        print(f"狀態碼: {response.status_code}")
        print(f"響應頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ JSON 響應成功:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失敗: {e}")
                print(f"響應內容: {response.text[:500]}")
        else:
            print(f"❌ API 請求失敗: {response.status_code}")
            print(f"響應內容: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 請求異常: {e}")

if __name__ == "__main__":
    print("🚀 開始測試數據修復 API...")
    print("=" * 50)
    
    test_data_status_api()
    test_data_recovery_api()
    
    print("\n" + "=" * 50)
    print("✅ 測試完成")
