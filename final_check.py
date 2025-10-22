#!/usr/bin/env python3
"""
最終檢查修復效果
"""

import time
import requests
import json

def final_check():
    """最終檢查修復效果"""
    print("最終檢查修復效果...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 等待部署完成
    print("等待Render重新部署...")
    for i in range(15):  # 等待最多2.5分鐘
        print(f"等待中... ({i+1}/15)")
        time.sleep(10)
        
        try:
            # 檢查API是否正常響應JSON
            response = requests.get(f"{base_url}/api/cash_management/transactions?page=1", timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ API正常響應JSON格式")
                    
                    # 檢查轉帳記錄
                    transactions = data.get('transactions', [])
                    transfer_records = [t for t in transactions if t.get('type') in ['TRANSFER_IN', 'TRANSFER_OUT']]
                    
                    if transfer_records:
                        print(f"✅ 找到 {len(transfer_records)} 筆轉帳記錄")
                        
                        # 檢查前3筆記錄
                        for i, record in enumerate(transfer_records[:3]):
                            print(f"\n轉帳記錄 {i+1}:")
                            print(f"  類型: {record.get('type')}")
                            print(f"  描述: {record.get('description')}")
                            print(f"  轉出帳戶: {record.get('payment_account', 'N/A')}")
                            print(f"  轉入帳戶: {record.get('deposit_account', 'N/A')}")
                            
                            # 檢查是否還有N/A
                            if (record.get('payment_account') == 'N/A' or 
                                record.get('deposit_account') == 'N/A'):
                                print("  ⚠️ 仍然顯示N/A")
                            else:
                                print("  ✅ 正確顯示帳戶名稱")
                        
                        # 檢查是否所有記錄都修復了
                        na_count = 0
                        for record in transfer_records:
                            if (record.get('payment_account') == 'N/A' or 
                                record.get('deposit_account') == 'N/A'):
                                na_count += 1
                        
                        if na_count == 0:
                            print(f"\n🎉 修復成功！所有 {len(transfer_records)} 筆轉帳記錄都正確顯示帳戶名稱")
                            return True
                        else:
                            print(f"\n⚠️ 仍有 {na_count} 筆記錄顯示N/A，可能需要更多時間")
                    else:
                        print("沒有找到轉帳記錄")
                except json.JSONDecodeError:
                    print("API響應不是JSON格式，繼續等待...")
                except Exception as e:
                    print(f"解析響應失敗: {e}")
            else:
                print(f"API響應失敗: {response.status_code}")
        except Exception as e:
            print(f"請求失敗: {e}")
    
    print("等待超時，請手動檢查線上環境")
    return False

def main():
    """主函數"""
    print("最終檢查修復效果")
    print("=" * 50)
    
    if final_check():
        print("\n🎉 修復完全成功！")
        print("現在可以訪問: https://rmb-sales-system-test1.onrender.com/admin/cash_management")
        print("轉帳記錄將正確顯示出入款帳戶，不再顯示N/A")
    else:
        print("\n請手動檢查線上環境或聯繫技術支援")

if __name__ == "__main__":
    main()
