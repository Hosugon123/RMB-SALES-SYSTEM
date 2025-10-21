#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API修復測試腳本
測試所有相關API是否正常工作
"""

import requests
import json
import time

def test_api_endpoint(name, url, timeout=30):
    """測試單個API端點"""
    print(f"\n🔍 測試 {name}...")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, timeout=timeout)
        print(f"📊 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ {name} 正常運作")
                print(f"📋 API狀態: {data.get('status', 'unknown')}")
                
                if 'data' in data and 'transactions' in data['data']:
                    transactions = data['data']['transactions']
                    print(f"📊 記錄數量: {len(transactions)}")
                    
                    if transactions:
                        print("📋 前3筆記錄:")
                        for i, record in enumerate(transactions[:3]):
                            print(f"  {i+1}. {record.get('type', 'N/A')} - {record.get('description', 'N/A')}")
                    else:
                        print("⚠️ 沒有記錄")
                else:
                    print("ℹ️ 無交易記錄數據")
                    
                return True
            except json.JSONDecodeError:
                print(f"❌ {name} 返回非JSON格式數據")
                print(f"📄 回應內容: {response.text[:200]}...")
                return False
        else:
            print(f"❌ {name} HTTP錯誤: {response.status_code}")
            print(f"📄 錯誤內容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ {name} 請求超時")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} 請求失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始測試API修復效果...")
    print("=" * 60)
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 測試的API端點
    apis = [
        ("交易記錄API", f"{base_url}/api/cash_management/transactions?page=1&per_page=5"),
        ("簡化API", f"{base_url}/api/cash_management/transactions_simple?page=1&per_page=5"),
        ("利潤歷史API", f"{base_url}/api/profit/history?page=1&per_page=5"),
    ]
    
    results = []
    
    for name, url in apis:
        result = test_api_endpoint(name, url)
        results.append((name, result))
        time.sleep(1)  # 避免請求過於頻繁
    
    # 總結結果
    print("\n" + "=" * 60)
    print("📋 測試結果總結:")
    
    success_count = 0
    for name, result in results:
        status = "✅ 正常" if result else "❌ 失敗"
        print(f"  {name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 總體結果: {success_count}/{len(results)} 個API正常運作")
    
    if success_count == len(results):
        print("🎉 所有API修復成功！")
        print("\n💡 建議:")
        print("  1. 檢查現金管理頁面是否正常載入")
        print("  2. 檢查利潤管理頁面是否正常顯示")
        print("  3. 如果仍有問題，請檢查應用程式日誌")
    else:
        print("⚠️ 部分API仍有問題，請檢查應用程式日誌")
        print("\n🔧 可能的解決方案:")
        print("  1. 重新部署應用程式")
        print("  2. 檢查資料庫連接")
        print("  3. 手動執行資料庫修復腳本")

if __name__ == '__main__':
    main()
