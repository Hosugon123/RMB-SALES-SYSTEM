#!/usr/bin/env python3
"""
測試現金頁面售出記錄的客戶應收帳款餘額變化數據
"""

import requests
import json

def test_cash_page_data():
    """測試現金頁面API返回的數據"""
    try:
        # 測試現金頁面API
        response = requests.get('http://localhost:5000/api/cash_management/transactions?page=1')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 現金頁面API請求成功")
            
            if data.get('status') == 'success':
                transactions = data.get('data', {}).get('transactions', [])
                print(f"📊 找到 {len(transactions)} 筆交易記錄")
                
                # 檢查售出記錄
                sales_records = [t for t in transactions if t.get('type') == '售出']
                print(f"🛒 找到 {len(sales_records)} 筆售出記錄")
                
                for i, sale in enumerate(sales_records):
                    print(f"\n--- 售出記錄 {i+1} ---")
                    print(f"描述: {sale.get('description', 'N/A')}")
                    print(f"客戶應收帳款餘額變化: {sale.get('customer_receivable_balance', 'N/A')}")
                    
                    if sale.get('customer_receivable_balance'):
                        balance = sale['customer_receivable_balance']
                        print(f"  變動前: {balance.get('before', 'N/A')}")
                        print(f"  變動: {balance.get('change', 'N/A')}")
                        print(f"  變動後: {balance.get('after', 'N/A')}")
                        print(f"  客戶名稱: {balance.get('customer_name', 'N/A')}")
                    else:
                        print("  ❌ 沒有客戶應收帳款餘額變化數據")
            else:
                print(f"❌ API返回錯誤: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP錯誤: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    print("開始測試現金頁面售出記錄的客戶應收帳款餘額變化數據...")
    test_cash_page_data()
