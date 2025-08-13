#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手動創建 card_purchases 表的腳本
"""

from app import app, db
from app import CardPurchase

def create_card_purchases_table():
    """創建 card_purchases 表"""
    with app.app_context():
        try:
            # 創建表
            db.create_all()
            print("✅ card_purchases 表已成功創建！")
            
            # 檢查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if 'card_purchases' in tables:
                print("✅ 確認 card_purchases 表存在於數據庫中")
            else:
                print("❌ card_purchases 表不存在於數據庫中")
                
        except Exception as e:
            print(f"❌ 創建表時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_card_purchases_table()
