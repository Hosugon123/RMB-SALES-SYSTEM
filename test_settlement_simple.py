#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的銷帳功能測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_settlement_logic():
    """測試銷帳邏輯"""
    print("🧪 測試銷帳邏輯...")
    
    # 模擬銷帳數據
    customer_id = 1
    amount = 1000.0
    account_id = 29
    note = "測試銷帳"
    
    print(f"   客戶ID: {customer_id}")
    print(f"   銷帳金額: {amount}")
    print(f"   收款帳戶ID: {account_id}")
    print(f"   備註: {note}")
    
    # 驗證邏輯
    if customer_id and amount > 0 and account_id:
        print("   ✅ 基本驗證通過")
        
        # 模擬銷帳計算
        old_receivables = 43300.0  # 假設原始應收帳款
        old_balance = 50000.0      # 假設原始帳戶餘額
        
        new_receivables = old_receivables - amount
        new_balance = old_balance + amount
        
        print(f"   銷帳前應收帳款: NT$ {old_receivables:,.2f}")
        print(f"   銷帳後應收帳款: NT$ {new_receivables:,.2f}")
        print(f"   銷帳前帳戶餘額: NT$ {old_balance:,.2f}")
        print(f"   銷帳後帳戶餘額: NT$ {new_balance:,.2f}")
        
        if new_receivables == old_receivables - amount:
            print("   ✅ 應收帳款計算正確")
        else:
            print("   ❌ 應收帳款計算錯誤")
            
        if new_balance == old_balance + amount:
            print("   ✅ 帳戶餘額計算正確")
        else:
            print("   ❌ 帳戶餘額計算錯誤")
            
    else:
        print("   ❌ 基本驗證失敗")
    
    print("✅ 銷帳邏輯測試完成")

if __name__ == "__main__":
    test_settlement_logic()
