#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試銷帳功能修復
驗證銷帳 API 是否正常工作
"""

import requests
import json
import time
from datetime import datetime

def test_settlement_api():
    """測試銷帳 API"""
    
    # 測試目標 URL
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    print("🧪 開始測試銷帳 API...")
    print(f"目標 URL: {base_url}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試資料
    test_data = {
        "customer_id": 1,
        "amount": 1.0,
        "account_id": 25,
        "note": "測試銷帳"
    }
    
    print(f"\n📋 測試資料:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    try:
        # 發送 POST 請求到銷帳 API
        print(f"\n🚀 發送請求到: {base_url}/api/settlement")
        
        response = requests.post(
            f"{base_url}/api/settlement",
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            json=test_data,
            timeout=30
        )
        
        print(f"📊 回應狀態碼: {response.status_code}")
        print(f"📊 回應標頭: {dict(response.headers)}")
        
        # 解析回應
        try:
            result = response.json()
            print(f"📊 回應內容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"📊 回應內容 (非 JSON): {response.text}")
        
        # 分析結果
        if response.status_code == 200:
            if result.get('status') == 'success':
                print("\n✅ 銷帳 API 測試成功！")
                return True
            else:
                print(f"\n⚠️ 銷帳 API 返回錯誤: {result.get('message', '未知錯誤')}")
                return False
        elif response.status_code == 500:
            print(f"\n❌ 銷帳 API 返回 500 內部伺服器錯誤")
            print("這表示後端代碼有問題，需要檢查伺服器日誌")
            return False
        elif response.status_code == 401:
            print(f"\n🔐 需要登入認證")
            print("這是正常的，因為銷帳 API 需要登入")
            return False
        else:
            print(f"\n⚠️ 銷帳 API 返回未預期的狀態碼: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ 請求超時")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n🌐 連接錯誤，無法連接到伺服器")
        return False
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        return False

def test_health_check():
    """測試健康檢查"""
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    print(f"\n🏥 測試健康檢查...")
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"健康檢查狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 應用程式正常運行")
            return True
        else:
            print("⚠️ 應用程式可能出現問題")
            return False
            
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始銷帳功能測試...")
    
    # 健康檢查
    health_ok = test_health_check()
    if not health_ok:
        print("❌ 應用程式無法訪問，測試終止")
        return False
    
    # 測試銷帳 API
    api_ok = test_settlement_api()
    
    print(f"\n📊 測試結果總結:")
    print(f"健康檢查: {'✅ 通過' if health_ok else '❌ 失敗'}")
    print(f"銷帳 API: {'✅ 通過' if api_ok else '❌ 失敗'}")
    
    if api_ok:
        print("\n🎉 銷帳功能測試通過！")
        print("建議進行完整的銷帳操作測試")
    else:
        print("\n💥 銷帳功能測試失敗")
        print("建議檢查伺服器日誌和資料庫狀態")
    
    return api_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
