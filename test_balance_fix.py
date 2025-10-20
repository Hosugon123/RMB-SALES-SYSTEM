#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試餘額計算修復
驗證上方帳戶總金額與下方交易紀錄的總額是否一致
"""

import requests
import json

def test_balance_consistency():
    """測試餘額一致性"""
    
    base_url = "http://localhost:5000"  # 本地測試
    # base_url = "https://rmb-sales-system-test1.onrender.com"  # 線上測試
    
    print("🧪 開始測試餘額一致性...")
    print(f"測試目標: {base_url}")
    
    try:
        # 測試 1: 獲取現金管理頁面總額
        print("\n📋 測試 1: 獲取現金管理頁面總額")
        response = requests.get(f"{base_url}/cash_management", timeout=10)
        if response.status_code == 200:
            print("✅ 現金管理頁面載入成功")
            
            # 從頁面中提取總額（需要解析HTML）
            content = response.text
            if "NT$ 1,245,407.79" in content:
                print("✅ 頁面顯示正確的總台幣金額: NT$ 1,245,407.79")
            else:
                print("❌ 頁面總台幣金額不正確")
        else:
            print(f"❌ 現金管理頁面載入失敗: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 現金管理頁面測試失敗: {e}")
    
    try:
        # 測試 2: 獲取交易記錄 API
        print("\n📋 測試 2: 獲取交易記錄 API")
        response = requests.get(f"{base_url}/api/cash_management/transactions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                transactions = data.get("data", {}).get("transactions", [])
                if transactions:
                    # 檢查第一筆交易的累積餘額
                    first_tx = transactions[0]
                    running_twd = first_tx.get("running_twd_balance", 0)
                    running_rmb = first_tx.get("running_rmb_balance", 0)
                    
                    print(f"✅ 第一筆交易累積餘額:")
                    print(f"   TWD: {running_twd:,.2f}")
                    print(f"   RMB: {running_rmb:,.2f}")
                    
                    # 檢查是否接近正確的總額
                    expected_twd = 1245407.79
                    if abs(running_twd - expected_twd) < 1:
                        print(f"✅ TWD 累積餘額正確: {running_twd:,.2f} ≈ {expected_twd:,.2f}")
                    else:
                        print(f"❌ TWD 累積餘額不正確: {running_twd:,.2f} ≠ {expected_twd:,.2f}")
                        print(f"   差異: {abs(running_twd - expected_twd):,.2f}")
                else:
                    print("⚠️ 沒有交易記錄可供測試")
            else:
                print(f"❌ 交易記錄 API 返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ 交易記錄 API 請求失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 交易記錄 API 測試失敗: {e}")
    
    try:
        # 測試 3: 獲取總額 API
        print("\n📋 測試 3: 獲取總額 API")
        response = requests.get(f"{base_url}/api/cash_management/totals", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                totals_data = data.get("data", {})
                api_total_twd = totals_data.get("total_twd", 0)
                api_total_rmb = totals_data.get("total_rmb", 0)
                
                print(f"✅ API 總額:")
                print(f"   TWD: {api_total_twd:,.2f}")
                print(f"   RMB: {api_total_rmb:,.2f}")
                
                # 檢查是否與預期一致
                expected_twd = 1245407.79
                if abs(api_total_twd - expected_twd) < 1:
                    print(f"✅ API TWD 總額正確: {api_total_twd:,.2f} ≈ {expected_twd:,.2f}")
                else:
                    print(f"❌ API TWD 總額不正確: {api_total_twd:,.2f} ≠ {expected_twd:,.2f}")
            else:
                print(f"❌ 總額 API 返回錯誤: {data.get('message', '未知錯誤')}")
        else:
            print(f"❌ 總額 API 請求失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 總額 API 測試失敗: {e}")
    
    print("\n🎯 測試完成！")
    print("\n📝 修復說明:")
    print("1. 修正了累積餘額計算邏輯：從實際帳戶餘額開始倒推")
    print("2. 統一了所有 API 端點的餘額計算方式")
    print("3. 確保交易記錄中的累積餘額與實際帳戶餘額一致")

if __name__ == '__main__':
    test_balance_consistency()
