#!/usr/bin/env python3
"""
Render 部署專用資料庫初始化腳本
在 Render 上部署後，手動執行此腳本來初始化資料庫
"""

import os
import sys
from app import app, db, User

def init_database():
    """初始化資料庫和創建預設管理員帳戶"""
    with app.app_context():
        try:
            # 創建所有表格
            db.create_all()
            print("✅ 資料庫表格創建成功")
            
            # 檢查是否已有管理員帳戶
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # 創建預設管理員帳戶
                admin_user = User(
                    username='admin',
                    role='admin',
                    is_active=True
                )
                admin_user.set_password('admin123')  # 預設密碼，請在首次登入後修改
                
                db.session.add(admin_user)
                db.session.commit()
                print("✅ 預設管理員帳戶創建成功")
                print("   用戶名: admin")
                print("   密碼: admin123")
                print("   ⚠️  請在首次登入後立即修改密碼！")
            else:
                print("✅ 管理員帳戶已存在")
                
        except Exception as e:
            print(f"❌ 資料庫初始化失敗: {e}")
            db.session.rollback()
            return False
            
        return True

if __name__ == "__main__":
    print("🚀 開始初始化 Render 資料庫...")
    if init_database():
        print("🎉 資料庫初始化完成！")
    else:
        print("💥 資料庫初始化失敗！")
        sys.exit(1)
