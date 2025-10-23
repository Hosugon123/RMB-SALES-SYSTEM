#!/usr/bin/env python3
"""
測試現金頁面API的客戶應收帳款餘額變化數據（帶認證）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from flask import Flask
import json

def test_cash_api_with_auth():
    """測試現金頁面API（帶認證）"""
    with app.test_client() as client:
        print("開始測試現金頁面API（帶認證）...")
        
        # 先登入
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        
        print(f"登入狀態碼: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # 測試API
            response = client.get('/api/cash_management/transactions?page=1')
            
            print(f"API狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.get_json()
                    print("API返回成功")
                    
                    if data.get('status') == 'success':
                        transactions = data.get('data', {}).get('transactions', [])
                        print(f"找到 {len(transactions)} 筆交易記錄")
                        
                        # 檢查售出記錄
                        sales_records = [t for t in transactions if t.get('type') == '售出']
                        print(f"其中 {len(sales_records)} 筆售出記錄")
                        
                        for i, sale in enumerate(sales_records):
                            print(f"\n售出記錄 {i+1}:")
                            print(f"  描述: {sale.get('description', 'N/A')}")
                            print(f"  客戶應收帳款餘額變化: {sale.get('customer_receivable_balance', 'N/A')}")
                            
                            if sale.get('customer_receivable_balance'):
                                balance = sale['customer_receivable_balance']
                                print(f"    變動前: {balance.get('before', 'N/A')}")
                                print(f"    變動: {balance.get('change', 'N/A')}")
                                print(f"    變動後: {balance.get('after', 'N/A')}")
                                print(f"    描述: {balance.get('description', 'N/A')}")
                            else:
                                print("    ❌ 沒有客戶應收帳款餘額變化數據")
                    else:
                        print(f"API返回錯誤: {data.get('message', 'Unknown error')}")
                except Exception as e:
                    print(f"解析JSON失敗: {e}")
                    print(f"原始回應: {response.get_data(as_text=True)}")
            else:
                print(f"API請求失敗: {response.status_code}")
                print(f"回應內容: {response.get_data(as_text=True)}")
        else:
            print("登入失敗")

if __name__ == "__main__":
    test_cash_api_with_auth()
