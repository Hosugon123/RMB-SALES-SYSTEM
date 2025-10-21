#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的利潤API測試
"""

import requests
import json

def test_profit_api():
    """測試利潤歷史API"""
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        print("🔍 測試利潤歷史API...")
        
        # 測試利潤歷史API
        response = requests.get(f"{base_url}/api/profit/history?page=1&per_page=10", timeout=30)
        
        print(f"📡 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API回應: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("status") == "success":
                transactions = data.get("data", {}).get("transactions", [])
                print(f"💰 利潤記錄數量: {len(transactions)}")
                
                if transactions:
                    print("📋 利潤記錄詳情:")
                    for i, record in enumerate(transactions):
                        print(f"  記錄 {i+1}: {record}")
                else:
                    print("⚠️ 沒有利潤記錄")
            else:
                print(f"❌ API返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ HTTP錯誤: {response.status_code}")
            print(f"回應內容: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == '__main__':
    test_profit_api()
