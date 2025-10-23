#!/usr/bin/env python3
"""
測試現金管理API的腳本
"""

import requests
import json
import sys

def test_cash_api():
    """測試現金管理API"""
    print("測試現金管理API")
    print("=" * 50)
    
    # 本地測試URL
    base_url = "http://localhost:5000"
    
    # 1. 先登入獲取session
    print("1. 嘗試登入...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # 登入
        login_response = session.post(f"{base_url}/login", data=login_data)
        print(f"   登入狀態碼: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("   [OK] 登入成功")
        else:
            print(f"   [ERROR] 登入失敗: {login_response.text}")
            return
        
        # 2. 測試現金管理API
        print("\n2. 測試現金管理API...")
        api_response = session.get(f"{base_url}/api/cash_management/transactions?page=1")
        print(f"   API狀態碼: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"   [OK] API調用成功")
            print(f"   狀態: {data.get('status')}")
            
            if data.get('status') == 'success':
                transactions = data.get('data', {}).get('transactions', [])
                pagination = data.get('data', {}).get('pagination', {})
                
                print(f"\n3. 交易記錄分析:")
                print(f"   總記錄數: {pagination.get('total_records', 0)}")
                print(f"   當前頁: {pagination.get('current_page', 0)}")
                print(f"   總頁數: {pagination.get('total_pages', 0)}")
                print(f"   本頁記錄數: {len(transactions)}")
                
                # 分析記錄類型
                record_types = {}
                for record in transactions:
                    record_type = record.get('type', '未知')
                    record_types[record_type] = record_types.get(record_type, 0) + 1
                
                print(f"\n4. 記錄類型統計:")
                for record_type, count in record_types.items():
                    print(f"   {record_type}: {count} 筆")
                
                # 顯示前5筆記錄的詳細信息
                print(f"\n5. 前5筆記錄詳情:")
                for i, record in enumerate(transactions[:5]):
                    print(f"   記錄 {i+1}:")
                    print(f"     類型: {record.get('type')}")
                    print(f"     日期: {record.get('date')}")
                    print(f"     描述: {record.get('description')}")
                    print(f"     TWD變動: {record.get('twd_change')}")
                    print(f"     RMB變動: {record.get('rmb_change')}")
                    print(f"     操作者: {record.get('operator')}")
                    print(f"     出款戶: {record.get('payment_account')}")
                    print(f"     入款戶: {record.get('deposit_account')}")
                    
                    # 檢查是否有利潤信息
                    if 'profit' in record:
                        print(f"     利潤: {record.get('profit')}")
                    if 'profit_change_detail' in record:
                        profit_detail = record.get('profit_change_detail', {})
                        print(f"     利潤詳情: {profit_detail}")
                    
                    # 檢查是否有餘額變化信息
                    if 'payment_account_balance' in record:
                        payment_balance = record.get('payment_account_balance', {})
                        print(f"     出款戶餘額: {payment_balance}")
                    if 'deposit_account_balance' in record:
                        deposit_balance = record.get('deposit_account_balance', {})
                        print(f"     入款戶餘額: {deposit_balance}")
                    
                    print()
                
                # 檢查是否有售出記錄
                sales_records = [r for r in transactions if r.get('type') == '售出']
                print(f"6. 售出記錄分析:")
                print(f"   售出記錄數: {len(sales_records)}")
                
                if sales_records:
                    print("   [OK] 找到售出記錄")
                    for i, record in enumerate(sales_records[:3]):
                        print(f"   售出記錄 {i+1}: {record.get('description')} - {record.get('date')}")
                else:
                    print("   [ERROR] 沒有找到售出記錄")
                
            else:
                print(f"   [ERROR] API返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"   [ERROR] API調用失敗: {api_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   [ERROR] 無法連接到服務器，請確保Flask應用正在運行")
        print("   請執行: python app.py")
    except Exception as e:
        print(f"   [ERROR] 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_cash_api()
