#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試銷帳功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Customer, CashAccount, User
from datetime import datetime

def test_settlement():
    """測試銷帳功能"""
    with app.app_context():
        try:
            print("🔍 開始測試銷帳功能...")
            
            # 1. 檢查客戶數據
            customers = Customer.query.filter_by(is_active=True).all()
            print(f"📋 找到 {len(customers)} 個活躍客戶:")
            for customer in customers:
                print(f"   - {customer.name} (ID: {customer.id}): NT$ {customer.total_receivables_twd:,.2f}")
            
            # 2. 檢查台幣帳戶
            twd_accounts = CashAccount.query.filter_by(currency='TWD', is_active=True).all()
            print(f"💰 找到 {len(twd_accounts)} 個台幣帳戶:")
            for account in twd_accounts:
                print(f"   - {account.name} (ID: {account.id}): NT$ {account.balance:,.2f}")
            
            # 3. 檢查用戶
            users = User.query.filter_by(is_active=True).all()
            print(f"👤 找到 {len(users)} 個活躍用戶:")
            for user in users:
                print(f"   - {user.username} (ID: {user.id})")
            
            # 4. 模擬銷帳操作
            if customers and twd_accounts and users:
                customer = customers[0]  # 使用第一個客戶
                account = twd_accounts[0]  # 使用第一個台幣帳戶
                user = users[0]  # 使用第一個用戶
                
                print(f"\n🧪 模擬銷帳操作:")
                print(f"   客戶: {customer.name}")
                print(f"   收款帳戶: {account.name}")
                print(f"   操作員: {user.username}")
                
                # 記錄銷帳前的狀態
                old_customer_balance = customer.total_receivables_twd
                old_account_balance = account.balance
                
                print(f"   銷帳前 - 客戶應收: NT$ {old_customer_balance:,.2f}")
                print(f"   銷帳前 - 帳戶餘額: NT$ {old_account_balance:,.2f}")
                
                # 執行銷帳
                amount = min(1000.0, old_customer_balance)  # 銷帳金額
                if amount > 0:
                    # 更新客戶應收帳款
                    customer.total_receivables_twd -= amount
                    
                    # 更新收款帳戶餘額
                    account.balance += amount
                    
                    # 提交事務
                    db.session.commit()
                    
                    # 刷新對象狀態
                    db.session.refresh(customer)
                    db.session.refresh(account)
                    
                    print(f"   銷帳金額: NT$ {amount:,.2f}")
                    print(f"   銷帳後 - 客戶應收: NT$ {customer.total_receivables_twd:,.2f}")
                    print(f"   銷帳後 - 帳戶餘額: NT$ {account.balance:,.2f}")
                    
                    # 驗證結果
                    if customer.total_receivables_twd == old_customer_balance - amount:
                        print("   ✅ 客戶應收帳款更新成功")
                    else:
                        print("   ❌ 客戶應收帳款更新失敗")
                    
                    if account.balance == old_account_balance + amount:
                        print("   ✅ 帳戶餘額更新成功")
                    else:
                        print("   ❌ 帳戶餘額更新失敗")
                    
                    # 回滾測試數據
                    customer.total_receivables_twd = old_customer_balance
                    account.balance = old_account_balance
                    db.session.commit()
                    print("   🔄 已回滾測試數據")
                else:
                    print("   ⚠️ 客戶無應收帳款，跳過銷帳測試")
            else:
                print("   ❌ 缺少必要的測試數據")
            
            print("\n✅ 銷帳功能測試完成")
            
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_settlement()
