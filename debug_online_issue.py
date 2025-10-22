#!/usr/bin/env python3
"""
調試線上環境問題
"""

import requests
import json

def debug_online_issue():
    """調試線上環境問題"""
    print("調試線上環境問題...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 檢查主頁面
        print("1. 檢查主頁面...")
        response = requests.get(base_url, timeout=10)
        print(f"   狀態碼: {response.status_code}")
        print(f"   內容類型: {response.headers.get('content-type', 'unknown')}")
        
        # 檢查現金管理頁面
        print("\n2. 檢查現金管理頁面...")
        response = requests.get(f"{base_url}/admin/cash_management", timeout=10)
        print(f"   狀態碼: {response.status_code}")
        print(f"   內容類型: {response.headers.get('content-type', 'unknown')}")
        
        # 檢查不同的API端點
        api_endpoints = [
            "/api/cash_management/transactions",
            "/api/cash_management/transactions?page=1",
            "/api/transactions",
            "/api/ledger_entries"
        ]
        
        for endpoint in api_endpoints:
            print(f"\n3. 檢查API端點: {endpoint}")
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                print(f"   狀態碼: {response.status_code}")
                print(f"   內容類型: {response.headers.get('content-type', 'unknown')}")
                
                if response.status_code == 200:
                    content = response.text[:200]
                    if content.startswith('{'):
                        print(f"   響應格式: JSON")
                        try:
                            data = response.json()
                            print(f"   響應數據: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                        except:
                            print(f"   響應數據: 無法解析JSON")
                    else:
                        print(f"   響應格式: HTML")
                        print(f"   響應內容: {content}...")
                else:
                    print(f"   錯誤響應: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   請求失敗: {e}")
        
        # 檢查是否有其他可用的API
        print(f"\n4. 檢查其他可能的API...")
        other_endpoints = [
            "/api/health",
            "/api/status", 
            "/api/test",
            "/health",
            "/status"
        ]
        
        for endpoint in other_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   找到可用端點: {endpoint} (狀態碼: {response.status_code})")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"調試失敗: {e}")
        return False

def main():
    """主函數"""
    print("調試線上環境問題")
    print("=" * 50)
    
    if debug_online_issue():
        print("\n調試完成")
    else:
        print("\n調試失敗")

if __name__ == "__main__":
    main()
