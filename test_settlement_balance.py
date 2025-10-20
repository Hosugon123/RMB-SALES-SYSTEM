#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試銷帳交易帳戶餘額變化修復
驗證 SETTLEMENT 交易是否正確記錄入款帳戶的餘額變化
"""

import requests
import json

def test_settlement_balance():
    """測試銷帳交易帳戶餘額變化"""
    
    base_url = "http://localhost:5000"  # 本地測試
    # base_url = "https://rmb-sales-system-test1.onrender.com"  # 線上測試
    
    print("🧪 開始測試銷帳交易帳戶餘額變化...")
    print(f"測試目標: {base_url}")
    
    try:
        # 測試 1: 獲取交易記錄 API
        print("\n📋 測試 1: 獲取交易記錄 API")
        response = requests.get(f"{base_url}/api/cash_management/transactions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                transactions = data.get("data", {}).get("transactions", [])
                print(f"✅ 成功獲取 {len(transactions)} 筆交易記錄")
                
                # 查找銷帳交易
                settlement_transactions = [tx for tx in transactions if tx.get("type") == "SETTLEMENT"]
                print(f"📊 找到 {len(settlement_transactions)} 筆銷帳交易")
                
                for i, tx in enumerate(settlement_transactions[:3]):  # 檢查前3筆
                    print(f"\n--- 銷帳交易 {i+1} ---")
                    print(f"時間: {tx.get('date', 'N/A')}")
                    print(f"描述: {tx.get('description', 'N/A')}")
                    print(f"金額: {tx.get('twd_change', 0):,.2f} TWD")
                    print(f"入款戶: {tx.get('deposit_account', 'N/A')}")
                    
                    # 檢查帳戶餘額變化
                    account_balance = tx.get("account_balance")
                    deposit_account_balance = tx.get("deposit_account_balance")
                    
                    if account_balance:
                        print(f"✅ 帳戶餘額變化:")
                        print(f"   前: {account_balance.get('before', 0):,.2f}")
                        print(f"   變動: {account_balance.get('change', 0):,.2f}")
                        print(f"   後: {account_balance.get('after', 0):,.2f}")
                    else:
                        print("❌ 缺少帳戶餘額變化信息")
                    
                    if deposit_account_balance:
                        print(f"✅ 入款戶餘額變化:")
                        print(f"   帳戶: {deposit_account_balance.get('account_name', 'N/A')}")
                        print(f"   前: {deposit_account_balance.get('before', 0):,.2f}")
                        print(f"   變動: {deposit_account_balance.get('change', 0):,.2f}")
                        print(f"   後: {deposit_account_balance.get('after', 0):,.2f}")
                    else:
                        print("❌ 缺少入款戶餘額變化信息")
                    
                    # 檢查是否為 0.00 問題
                    if account_balance and account_balance.get('before') == 0 and account_balance.get('after') == 0:
                        print("⚠️ 警告: 帳戶餘額變化顯示為 0.00，可能仍有問題")
                    elif deposit_account_balance and deposit_account_balance.get('before') == 0 and deposit_account_balance.get('after') == 0:
                        print("⚠️ 警告: 入款戶餘額變化顯示為 0.00，可能仍有問題")
                    else:
                        print("✅ 帳戶餘額變化正常")
                
            else:
                print(f"❌ 交易記錄 API 返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ 交易記錄 API 請求失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 交易記錄 API 測試失敗: {e}")
    
    print("\n🎯 測試完成！")
    print("\n📝 修復說明:")
    print("1. 改進了 SETTLEMENT 交易的帳戶餘額變化記錄")
    print("2. 增強了 matching_entry 的查找邏輯（時間範圍和金額匹配）")
    print("3. 添加了 deposit_account_balance 字段來記錄入款戶餘額變化")
    print("4. 確保銷帳交易能正確顯示入款帳戶的前後餘額")

if __name__ == '__main__':
    test_settlement_balance()
