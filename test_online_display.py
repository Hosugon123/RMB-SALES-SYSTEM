#!/usr/bin/env python3
"""
測試線上環境的轉帳記錄顯示
"""

import requests
import json

def test_online_display():
    """測試線上環境的轉帳記錄顯示"""
    print("測試線上環境的轉帳記錄顯示...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 測試現金管理頁面的API
        response = requests.get(f"{base_url}/api/cash_management/transactions?page=1", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API響應成功，狀態碼: {response.status_code}")
            
            # 檢查轉帳記錄
            transactions = data.get('transactions', [])
            print(f"找到 {len(transactions)} 筆交易記錄")
            
            transfer_records = [t for t in transactions if t.get('type') in ['TRANSFER_IN', 'TRANSFER_OUT']]
            print(f"其中轉帳記錄: {len(transfer_records)} 筆")
            
            for i, record in enumerate(transfer_records[:5]):  # 只顯示前5筆
                print(f"\n轉帳記錄 {i+1}:")
                print(f"  類型: {record.get('type')}")
                print(f"  描述: {record.get('description')}")
                print(f"  轉出帳戶: {record.get('payment_account', 'N/A')}")
                print(f"  轉入帳戶: {record.get('deposit_account', 'N/A')}")
                
                # 檢查餘額詳情
                if 'payment_account_balance' in record:
                    balance = record['payment_account_balance']
                    print(f"  轉出帳戶餘額: 前={balance.get('before', 'N/A')}, 變動={balance.get('change', 'N/A')}, 後={balance.get('after', 'N/A')}")
                
                if 'deposit_account_balance' in record:
                    balance = record['deposit_account_balance']
                    print(f"  轉入帳戶餘額: 前={balance.get('before', 'N/A')}, 變動={balance.get('change', 'N/A')}, 後={balance.get('after', 'N/A')}")
            
            return True
        else:
            print(f"API響應失敗，狀態碼: {response.status_code}")
            print(f"響應內容: {response.text}")
            return False
            
    except Exception as e:
        print(f"測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("測試線上環境轉帳記錄顯示")
    print("=" * 50)
    
    if test_online_display():
        print("\n測試完成")
    else:
        print("\n測試失敗")

if __name__ == "__main__":
    main()
