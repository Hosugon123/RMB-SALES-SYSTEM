#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試現金管理頁面累積餘額修復的腳本
"""

import requests
import json
from datetime import datetime

def test_cash_management_api():
    """測試現金管理 API 是否正確返回累積餘額"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 開始測試現金管理 API...")
    
    try:
        # 測試獲取交易記錄
        print("\n1. 測試獲取交易記錄 API...")
        response = requests.get(f"{base_url}/api/cash_management/transactions?page=1")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 響應成功: {data['status']}")
            
            if data['status'] == 'success':
                transactions = data['data']['transactions']
                pagination = data['data']['pagination']
                
                print(f"📊 分頁信息: 第 {pagination['current_page']} 頁，共 {pagination['total_records']} 筆記錄")
                print(f"📋 交易記錄數量: {len(transactions)}")
                
                # 檢查累積餘額字段
                if transactions:
                    first_transaction = transactions[0]
                    print(f"\n🔍 第一筆交易記錄檢查:")
                    print(f"   類型: {first_transaction.get('type', 'N/A')}")
                    print(f"   日期: {first_transaction.get('date', 'N/A')}")
                    print(f"   TWD 變動: {first_transaction.get('twd_change', 'N/A')}")
                    print(f"   RMB 變動: {first_transaction.get('rmb_change', 'N/A')}")
                    
                    # 檢查累積餘額字段是否存在
                    running_twd = first_transaction.get('running_twd_balance')
                    running_rmb = first_transaction.get('running_rmb_balance')
                    
                    if running_twd is not None and running_rmb is not None:
                        print(f"✅ 累積餘額字段存在:")
                        print(f"   累積 TWD 餘額: {running_twd}")
                        print(f"   累積 RMB 餘額: {running_rmb}")
                    else:
                        print("❌ 累積餘額字段缺失!")
                        print(f"   running_twd_balance: {running_twd}")
                        print(f"   running_rmb_balance: {running_rmb}")
                    
                    # 檢查所有記錄是否都有累積餘額
                    missing_balance = 0
                    for i, trans in enumerate(transactions):
                        if 'running_twd_balance' not in trans or 'running_rmb_balance' not in trans:
                            missing_balance += 1
                            print(f"   ❌ 第 {i+1} 筆記錄缺少累積餘額")
                    
                    if missing_balance == 0:
                        print(f"✅ 所有 {len(transactions)} 筆記錄都包含累積餘額")
                    else:
                        print(f"❌ 有 {missing_balance} 筆記錄缺少累積餘額")
                else:
                    print("⚠️ 沒有交易記錄")
            else:
                print(f"❌ API 返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            print(f"響應內容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保應用程序正在運行")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

def test_totals_api():
    """測試總資產 API"""
    
    base_url = "http://localhost:5000"
    
    print("\n2. 測試總資產 API...")
    
    try:
        response = requests.get(f"{base_url}/api/cash_management/totals")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 總資產 API 響應成功")
            print(f"   總 TWD: {data.get('total_twd', 'N/A')}")
            print(f"   總 RMB: {data.get('total_rmb', 'N/A')}")
            print(f"   應收帳款: {data.get('total_receivables_twd', 'N/A')}")
        else:
            print(f"❌ 總資產 API HTTP 錯誤: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器")
    except Exception as e:
        print(f"❌ 測試總資產 API 時發生錯誤: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 現金管理頁面累積餘額修復測試")
    print("=" * 60)
    
    test_cash_management_api()
    test_totals_api()
    
    print("\n" + "=" * 60)
    print("🏁 測試完成")
    print("=" * 60)
