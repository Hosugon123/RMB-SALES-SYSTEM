#!/usr/bin/env python3
"""
PostgreSQL修復測試腳本
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_settlement_api():
    """測試銷帳API"""
    print("🧪 測試銷帳API...")
    
    # 線上環境URL
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 測試數據
    test_data = {
        "customer_id": 1,
        "amount": 0.01,  # 使用很小的金額進行測試
        "account_id": 25,
        "note": "PostgreSQL修復測試"
    }
    
    try:
        print(f"📡 發送測試請求到: {base_url}/api/settlement")
        print(f"📡 測試數據: {test_data}")
        
        # 發送POST請求
        response = requests.post(
            f"{base_url}/api/settlement",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 HTTP狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功回應: {result}")
            return True
        else:
            print(f"❌ 錯誤回應: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def check_application_status():
    """檢查應用程式狀態"""
    print("🔍 檢查應用程式狀態...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 檢查根路徑
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"📡 應用程式狀態: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 應用程式正常運行")
            return True
        else:
            print("❌ 應用程式異常")
            return False
            
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False

def main():
    """主函數"""
    print("PostgreSQL修復測試")
    print("=" * 50)
    
    # 1. 檢查應用程式狀態
    if not check_application_status():
        print("❌ 應用程式未正常運行")
        return False
    
    # 2. 測試銷帳API
    if test_settlement_api():
        print("\n🎉 PostgreSQL修復成功！")
        print("✅ 銷帳API現在可以正常工作")
        print("✅ 欄位問題已解決")
        return True
    else:
        print("\n❌ 修復可能未完全成功")
        print("建議檢查Render服務日誌")
        return False

if __name__ == "__main__":
    main()
