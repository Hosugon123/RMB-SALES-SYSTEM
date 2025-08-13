#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
調試版本的創建表腳本
"""

print("開始執行腳本...")

try:
    print("導入 app...")
    from app import app, db
    print("✅ 成功導入 app 和 db")
    
    print("導入 CardPurchase 模型...")
    from app import CardPurchase
    print("✅ 成功導入 CardPurchase 模型")
    
    print("檢查模型定義...")
    print(f"CardPurchase 表名: {CardPurchase.__tablename__}")
    print(f"CardPurchase 列: {[c.name for c in CardPurchase.__table__.columns]}")
    
    print("進入應用程序上下文...")
    with app.app_context():
        print("✅ 已進入應用程序上下文")
        
        print("檢查現有表...")
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"現有表: {existing_tables}")
        
        print("創建所有表...")
        db.create_all()
        print("✅ db.create_all() 執行完成")
        
        print("再次檢查表...")
        inspector = db.inspect(db.engine)
        updated_tables = inspector.get_table_names()
        print(f"更新後的表: {updated_tables}")
        
        if 'card_purchases' in updated_tables:
            print("✅ card_purchases 表已成功創建！")
        else:
            print("❌ card_purchases 表仍然不存在")
            
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()

print("腳本執行完成")
