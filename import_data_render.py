#!/usr/bin/env python3
"""
Render雲端數據導入腳本
用於將本地導出的JSON數據導入到Render的PostgreSQL數據庫
"""

import json
import os
from datetime import datetime
from sqlalchemy import text

# 確保在應用程式上下文中運行
def import_database_from_json():
    """從JSON文件導入數據到數據庫"""
    
    # 導入Flask應用程式和數據庫模型
    from app import app, db, User, Holder, CashAccount, Customer, Channel
    
    with app.app_context():
        print("🔍 尋找數據導出文件...")
        
        # 尋找導出文件
        json_files = [f for f in os.listdir('.') if f.startswith('database_export') and f.endswith('.json')]
        
        if not json_files:
            print("❌ 未找到數據導出文件 (database_export*.json)")
            return False
            
        # 使用最新的文件
        json_file = sorted(json_files)[-1]
        print(f"📁 找到導出文件: {json_file}")
        
        try:
            # 讀取JSON數據
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 數據統計:")
            print(f"   👥 用戶: {len(data.get('users', []))}")
            print(f"   🏢 持有人: {len(data.get('holders', []))}")
            print(f"   💰 現金帳戶: {len(data.get('cash_accounts', []))}")
            print(f"   👤 客戶: {len(data.get('customers', []))}")
            print(f"   📡 渠道: {len(data.get('channels', []))}")
            
            # 開始導入
            print("\n🚀 開始導入數據...")
            
            # 1. 導入用戶
            print("📥 導入用戶...")
            for user_data in data.get('users', []):
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    user = User(
                        username=user_data['username'],
                        password_hash='pbkdf2:sha256:260000$default$hash',  # 默認密碼hash
                        is_admin=user_data.get('is_admin', False),
                        is_active=user_data.get('is_active', True)
                    )
                    db.session.add(user)
                    print(f"   ✅ 新增用戶: {user_data['username']}")
                else:
                    print(f"   ⚠️ 用戶已存在: {user_data['username']}")
            
            # 2. 導入持有人
            print("📥 導入持有人...")
            for holder_data in data.get('holders', []):
                existing_holder = Holder.query.filter_by(name=holder_data['name']).first()
                if not existing_holder:
                    holder = Holder(
                        name=holder_data['name'],
                        is_active=holder_data.get('is_active', True)
                    )
                    db.session.add(holder)
                    print(f"   ✅ 新增持有人: {holder_data['name']}")
                else:
                    print(f"   ⚠️ 持有人已存在: {holder_data['name']}")
            
            # 提交持有人數據，以便後續引用
            db.session.commit()
            
            # 3. 導入現金帳戶
            print("📥 導入現金帳戶...")
            for account_data in data.get('cash_accounts', []):
                existing_account = CashAccount.query.filter_by(name=account_data['name']).first()
                if not existing_account:
                    # 查找對應的持有人
                    holder = None
                    if account_data.get('holder_name'):
                        holder = Holder.query.filter_by(name=account_data['holder_name']).first()
                    
                    account = CashAccount(
                        name=account_data['name'],
                        currency=account_data['currency'],
                        balance=account_data.get('balance', 0.0),
                        holder_id=holder.id if holder else None
                    )
                    db.session.add(account)
                    print(f"   ✅ 新增帳戶: {account_data['name']} ({account_data['currency']})")
                else:
                    # 更新餘額
                    existing_account.balance = account_data.get('balance', 0.0)
                    print(f"   🔄 更新帳戶餘額: {account_data['name']}")
            
            # 4. 導入客戶
            print("📥 導入客戶...")
            for customer_data in data.get('customers', []):
                existing_customer = Customer.query.filter_by(name=customer_data['name']).first()
                if not existing_customer:
                    customer = Customer(
                        name=customer_data['name'],
                        is_active=customer_data.get('is_active', True),
                        total_receivables_twd=customer_data.get('total_receivables_twd', 0.0)
                    )
                    db.session.add(customer)
                    print(f"   ✅ 新增客戶: {customer_data['name']}")
                else:
                    # 更新應收帳款
                    existing_customer.total_receivables_twd = customer_data.get('total_receivables_twd', 0.0)
                    print(f"   🔄 更新客戶: {customer_data['name']}")
            
            # 5. 導入渠道
            print("📥 導入渠道...")
            for channel_data in data.get('channels', []):
                existing_channel = Channel.query.filter_by(name=channel_data['name']).first()
                if not existing_channel:
                    channel = Channel(
                        name=channel_data['name'],
                        is_active=channel_data.get('is_active', True)
                    )
                    db.session.add(channel)
                    print(f"   ✅ 新增渠道: {channel_data['name']}")
                else:
                    print(f"   ⚠️ 渠道已存在: {channel_data['name']}")
            
            # 最終提交
            db.session.commit()
            
            print(f"\n🎉 數據導入完成！")
            print(f"📅 導入時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 導入失敗: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = import_database_from_json()
    if success:
        print("✅ 數據導入成功完成！")
    else:
        print("❌ 數據導入失敗！")
