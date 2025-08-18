#!/usr/bin/env python3
"""
為 Customer 表添加 created_at 欄位的遷移腳本
這個腳本會安全地添加欄位，為現有記錄設置默認時間
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

def add_created_at_column():
    """為Customer表安全地添加created_at欄位"""
    
    # 獲取數據庫連接字串
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 錯誤：找不到 DATABASE_URL 環境變量")
        return False
    
    # 修正數據庫連接字串格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif not database_url.startswith('postgresql+psycopg://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    try:
        # 創建數據庫引擎
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 檢查created_at欄位是否已存在
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('customers')]
            
            if 'created_at' in columns:
                print("✅ created_at 欄位已存在，無需遷移")
                return True
            
            print("🔄 開始為 customers 表添加 created_at 欄位...")
            
            # 開始事務
            trans = conn.begin()
            
            try:
                # 添加created_at欄位，允許NULL
                conn.execute(text("""
                    ALTER TABLE customers 
                    ADD COLUMN created_at TIMESTAMP NULL
                """))
                
                # 為現有記錄設置創建時間（使用當前時間）
                conn.execute(text("""
                    UPDATE customers 
                    SET created_at = CURRENT_TIMESTAMP 
                    WHERE created_at IS NULL
                """))
                
                print("✅ 成功添加 created_at 欄位並設置默認值")
                
                # 提交事務
                trans.commit()
                
                # 驗證
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM customers 
                    WHERE created_at IS NOT NULL
                """))
                count = result.fetchone()[0]
                print(f"✅ 驗證完成：{count} 個客戶記錄已有 created_at 值")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ 事務回滾：{e}")
                return False
            
    except (SQLAlchemyError, ProgrammingError) as e:
        print(f"❌ 數據庫錯誤：{e}")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤：{e}")
        return False

if __name__ == '__main__':
    print("🚀 開始添加 Customer.created_at 欄位...")
    success = add_created_at_column()
    
    if success:
        print("✅ 遷移完成！客戶管理功能現在可以正常使用了。")
        sys.exit(0)
    else:
        print("❌ 遷移失敗！")
        sys.exit(1)
