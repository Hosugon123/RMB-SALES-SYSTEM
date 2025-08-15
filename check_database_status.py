#!/usr/bin/env python3
"""
檢查數據庫狀態和內容
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Holder, CashAccount, Customer, Channel

def check_database_status():
    """檢查數據庫狀態"""
    with app.app_context():
        print("🔍 檢查數據庫狀態...")
        print(f"📍 數據庫位置: {app.config.get('SQLALCHEMY_DATABASE_URI', '未設定')}")
        
        try:
            # 檢查用戶表
            users = db.session.execute(db.select(User)).scalars().all()
            print(f"👥 用戶: {len(users)} 個")
            for user in users:
                print(f"   - {user.username} ({'管理員' if user.is_admin else '普通用戶'})")
            
            # 檢查持有人表
            holders = db.session.execute(db.select(Holder)).scalars().all()
            print(f"🏢 持有人: {len(holders)} 個")
            for holder in holders:
                print(f"   - {holder.name}")
            
            # 檢查現金帳戶表
            accounts = db.session.execute(db.select(CashAccount)).scalars().all()
            print(f"💰 現金帳戶: {len(accounts)} 個")
            total_twd = sum(acc.balance for acc in accounts if acc.currency == "TWD")
            total_rmb = sum(acc.balance for acc in accounts if acc.currency == "RMB")
            print(f"   總台幣: NT$ {total_twd:,.2f}")
            print(f"   總人民幣: ¥ {total_rmb:,.2f}")
            
            # 檢查客戶表
            try:
                customers = db.session.execute(db.select(Customer)).scalars().all()
                print(f"👤 客戶: {len(customers)} 個")
                total_receivables = sum(c.total_receivables_twd for c in customers)
                print(f"   總應收: NT$ {total_receivables:,.2f}")
            except Exception as e:
                print(f"❌ 客戶表查詢失敗: {e}")
            
            # 檢查渠道表
            try:
                channels = db.session.execute(db.select(Channel)).scalars().all()
                print(f"📡 渠道: {len(channels)} 個")
            except Exception as e:
                print(f"❌ 渠道表查詢失敗: {e}")
                
        except Exception as e:
            print(f"❌ 數據庫檢查失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_database_status()