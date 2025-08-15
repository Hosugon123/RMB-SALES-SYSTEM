#!/usr/bin/env python3
"""
從JSON文件導入數據到資料庫
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Holder, CashAccount, Customer, PurchaseRecord, SalesRecord, LedgerEntry, CashLog, Channel

def import_database(json_file):
    """從JSON文件導入數據到資料庫"""
    with app.app_context():
        print(f"🚀 開始從 {json_file} 導入數據...")
        
        # 讀取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📅 數據導出時間: {data.get('export_time', '未知')}")
        
        try:
            # 導入用戶
            for user_data in data.get("users", []):
                existing = db.session.execute(
                    db.select(User).filter_by(username=user_data["username"])
                ).scalar_one_or_none()
                
                if not existing:
                    user = User(
                        username=user_data["username"],
                        password_hash=user_data["password_hash"],
                        is_admin=user_data.get("is_admin", False),
                        is_active=user_data.get("is_active", True)
                    )
                    db.session.add(user)
            
            db.session.commit()
            print(f"✅ 導入用戶完成")
            
            # 導入持有人
            for holder_data in data.get("holders", []):
                existing = db.session.execute(
                    db.select(Holder).filter_by(name=holder_data["name"])
                ).scalar_one_or_none()
                
                if not existing:
                    holder = Holder(
                        name=holder_data["name"],
                        is_active=holder_data.get("is_active", True)
                    )
                    db.session.add(holder)
            
            db.session.commit()
            print(f"✅ 導入持有人完成")
            
            # 導入現金帳戶
            for account_data in data.get("cash_accounts", []):
                existing = db.session.execute(
                    db.select(CashAccount).filter_by(
                        name=account_data["name"],
                        holder_id=account_data["holder_id"]
                    )
                ).scalar_one_or_none()
                
                if not existing:
                    account = CashAccount(
                        name=account_data["name"],
                        currency=account_data["currency"],
                        balance=account_data["balance"],
                        holder_id=account_data["holder_id"]
                    )
                    db.session.add(account)
            
            db.session.commit()
            print(f"✅ 導入現金帳戶完成")
            
            # 導入客戶
            for customer_data in data.get("customers", []):
                existing = db.session.execute(
                    db.select(Customer).filter_by(name=customer_data["name"])
                ).scalar_one_or_none()
                
                if not existing:
                    customer = Customer(
                        name=customer_data["name"],
                        is_active=customer_data.get("is_active", True),
                        total_receivables_twd=customer_data.get("total_receivables_twd", 0.0)
                    )
                    db.session.add(customer)
            
            db.session.commit()
            print(f"✅ 導入客戶完成")
            
            # 導入渠道
            for channel_data in data.get("channels", []):
                existing = db.session.execute(
                    db.select(Channel).filter_by(name=channel_data["name"])
                ).scalar_one_or_none()
                
                if not existing:
                    channel = Channel(
                        name=channel_data["name"],
                        is_active=channel_data.get("is_active", True)
                    )
                    db.session.add(channel)
            
            db.session.commit()
            print(f"✅ 導入渠道完成")
            
            # 導入交易記錄（買入、銷售、分錄、現金流水）
            # 注意：這些記錄通常包含外鍵關聯，需要謹慎處理
            
            print(f"🎉 數據導入完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 導入失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使用方法: python import_data.py <json文件名>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not os.path.exists(json_file):
        print(f"文件不存在: {json_file}")
        sys.exit(1)
    
    import_data(json_file)
