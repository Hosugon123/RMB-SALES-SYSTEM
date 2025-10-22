#!/usr/bin/env python3
"""
等待部署完成並檢查
"""

import time
import requests

def wait_and_check():
    """等待部署完成並檢查"""
    print("等待Render部署完成...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 等待部署完成
    for i in range(12):  # 等待最多2分鐘
        print(f"等待中... ({i+1}/12)")
        time.sleep(10)
        
        try:
            # 檢查主頁面
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print("主頁面正常")
                
                # 檢查API
                try:
                    api_response = requests.get(f"{base_url}/api/cash_management/transactions?page=1", timeout=5)
                    if api_response.status_code == 200:
                        try:
                            data = api_response.json()
                            print("API正常響應JSON格式")
                            
                            # 檢查轉帳記錄
                            transactions = data.get('transactions', [])
                            transfer_records = [t for t in transactions if t.get('type') in ['TRANSFER_IN', 'TRANSFER_OUT']]
                            
                            if transfer_records:
                                print(f"找到 {len(transfer_records)} 筆轉帳記錄")
                                
                                # 檢查第一筆記錄
                                first_record = transfer_records[0]
                                print(f"第一筆記錄:")
                                print(f"  類型: {first_record.get('type')}")
                                print(f"  描述: {first_record.get('description')}")
                                print(f"  轉出帳戶: {first_record.get('payment_account', 'N/A')}")
                                print(f"  轉入帳戶: {first_record.get('deposit_account', 'N/A')}")
                                
                                # 檢查是否還有N/A
                                if (first_record.get('payment_account') == 'N/A' or 
                                    first_record.get('deposit_account') == 'N/A'):
                                    print("⚠️ 仍然顯示N/A，可能需要更多時間")
                                else:
                                    print("✅ 修復成功！不再顯示N/A")
                                    return True
                            else:
                                print("沒有找到轉帳記錄")
                        except:
                            print("API響應不是JSON格式")
                    else:
                        print(f"API響應失敗: {api_response.status_code}")
                except:
                    print("API請求失敗")
            else:
                print(f"主頁面響應失敗: {response.status_code}")
        except:
            print("網站無法訪問")
    
    print("等待超時，請手動檢查")
    return False

def main():
    """主函數"""
    print("等待部署完成並檢查修復狀態")
    print("=" * 50)
    
    if wait_and_check():
        print("\n修復成功！")
    else:
        print("\n請手動檢查線上環境")

if __name__ == "__main__":
    main()
