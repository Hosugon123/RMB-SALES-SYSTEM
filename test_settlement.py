#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試銷帳功能的腳本
"""

import requests
import json

def test_settlement():
    """測試銷帳功能"""
    
    # 測試數據
    test_data = {
        "customer_id": 1,
        "account_id": 1,
        "amount": 5.0,
        "note": "測試銷帳"
    }
    
    try:
        # 發送銷帳請求
        response = requests.post(
            "http://127.0.0.1:5000/api/settlement",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 銷帳成功: {result.get('message')}")
        else:
            print(f"❌ 銷帳失敗: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保 Flask 應用正在運行")
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

if __name__ == "__main__":
    print("🧪 開始測試銷帳功能...")
    test_settlement()
