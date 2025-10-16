#!/usr/bin/env python3
"""
部屬環境資料庫修復腳本
修復 purchase_records 表缺少 payment_status 欄位的問題
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def create_app():
    """創建 Flask 應用程式實例"""
    app = Flask(__name__)
    
    # 資料庫配置
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        # 修復 Render PostgreSQL URL 格式問題
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        print("❌ 未找到 DATABASE_URL 環境變數")
        return None
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

def fix_database():
    """修復資料庫"""
    print("🚀 開始修復部屬環境資料庫...")
    
    # 創建應用程式
    app = create_app()
    if not app:
        return False
    
    with app.app_context():
        from sqlalchemy import text
        
        try:
            # 獲取資料庫連接
            from app import db
            engine = db.engine
            
            print("🔗 連接到資料庫...")
            
            with engine.connect() as conn:
                # 檢查 purchase_records 表是否存在
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'purchase_records'
                    );
                """))
                
                if not result.scalar():
                    print("❌ purchase_records 表不存在")
                    return False
                
                # 檢查 payment_status 欄位是否存在
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'purchase_records' 
                        AND column_name = 'payment_status'
                    );
                """))
                
                if result.scalar():
                    print("✅ payment_status 欄位已存在")
                    return True
                
                print("🔧 新增 payment_status 欄位...")
                
                # 開始事務
                trans = conn.begin()
                try:
                    # 新增欄位
                    conn.execute(text("""
                        ALTER TABLE purchase_records 
                        ADD COLUMN payment_status VARCHAR(20) DEFAULT 'paid' NOT NULL;
                    """))
                    
                    # 更新現有記錄
                    conn.execute(text("""
                        UPDATE purchase_records 
                        SET payment_status = 'paid' 
                        WHERE payment_status IS NULL;
                    """))
                    
                    # 移除預設值
                    conn.execute(text("""
                        ALTER TABLE purchase_records 
                        ALTER COLUMN payment_status DROP DEFAULT;
                    """))
                    
                    # 提交事務
                    trans.commit()
                    print("✅ 成功修復資料庫！")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            print(f"❌ 修復失敗: {e}")
            return False

if __name__ == "__main__":
    success = fix_database()
    
    if success:
        print("\n🎉 修復完成！現在可以重新載入頁面了。")
        print("請重新整理以下頁面：")
        print("- 儀表板 (/dashboard)")
        print("- 買入頁面 (/buy-in)")
        print("- 現金管理 (/cash-management)")
        sys.exit(0)
    else:
        print("\n💥 修復失敗，請檢查錯誤訊息。")
        sys.exit(1)


