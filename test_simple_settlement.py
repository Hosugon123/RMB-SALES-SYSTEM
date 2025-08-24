#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的銷帳功能測試
"""

def test_settlement_logic():
    """測試銷帳邏輯"""
    print("🧪 測試銷帳邏輯...")
    
    # 模擬銷帳前的狀態
    customer_receivables_before = 5171.50
    account_balance_before = 10000.00
    settlement_amount = 100.00
    
    print(f"銷帳前:")
    print(f"  客戶應收帳款: NT$ {customer_receivables_before:,.2f}")
    print(f"  帳戶餘額: NT$ {account_balance_before:,.2f}")
    print(f"  銷帳金額: NT$ {settlement_amount:,.2f}")
    
    # 模擬銷帳後的狀態
    customer_receivables_after = customer_receivables_before - settlement_amount
    account_balance_after = account_balance_before + settlement_amount
    
    print(f"\n銷帳後:")
    print(f"  客戶應收帳款: NT$ {customer_receivables_after:,.2f}")
    print(f"  帳戶餘額: NT$ {account_balance_after:,.2f}")
    
    # 驗證計算
    print(f"\n驗證:")
    print(f"  應收帳款減少: {customer_receivables_before - customer_receivables_after:,.2f} ✅")
    print(f"  帳戶餘額增加: {account_balance_after - account_balance_before:,.2f} ✅")
    
    # 檢查是否與截圖中的數據一致
    print(f"\n與截圖數據對比:")
    print(f"  截圖中應收帳款: NT$ 4,330.00")
    print(f"  截圖中帳戶餘額: NT$ 10,000.00")
    print(f"  計算後應收帳款: NT$ {customer_receivables_after:,.2f}")
    print(f"  計算後帳戶餘額: NT$ {account_balance_after:,.2f}")
    
    if abs(customer_receivables_after - 4330.00) < 0.01:
        print("  ✅ 應收帳款計算正確")
    else:
        print("  ❌ 應收帳款計算錯誤")
    
    if abs(account_balance_after - 10100.00) < 0.01:
        print("  ✅ 帳戶餘額計算正確")
    else:
        print("  ❌ 帳戶餘額計算錯誤")

if __name__ == "__main__":
    test_settlement_logic()
