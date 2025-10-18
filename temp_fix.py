#!/usr/bin/env python3
"""
臨時修復：修改查詢以排除 payment_status 欄位
這是一個臨時解決方案，直到資料庫修復完成
"""
import re

def create_temp_fix():
    """創建臨時修復補丁"""
    
    # 讀取 app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 備份原文件
    with open('app.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修改儀表板查詢
    old_query = """        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord)
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )"""
    
    new_query = """        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord.id, PurchaseRecord.payment_account_id, 
                         PurchaseRecord.deposit_account_id, PurchaseRecord.channel_id,
                         PurchaseRecord.rmb_amount, PurchaseRecord.exchange_rate,
                         PurchaseRecord.twd_cost, PurchaseRecord.purchase_date,
                         PurchaseRecord.operator_id)
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(5)
            )
            .all()
        )"""
    
    content = content.replace(old_query, new_query)
    
    # 修改買入頁面查詢
    old_buyin_query = """        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord)
                .options(
                    db.selectinload(PurchaseRecord.channel),
                    db.selectinload(PurchaseRecord.payment_account),
                    db.selectinload(PurchaseRecord.deposit_account),
                    db.selectinload(PurchaseRecord.operator)
                )
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )"""
    
    new_buyin_query = """        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord.id, PurchaseRecord.payment_account_id,
                         PurchaseRecord.deposit_account_id, PurchaseRecord.channel_id,
                         PurchaseRecord.rmb_amount, PurchaseRecord.exchange_rate,
                         PurchaseRecord.twd_cost, PurchaseRecord.purchase_date,
                         PurchaseRecord.operator_id)
                .options(
                    db.selectinload(PurchaseRecord.channel),
                    db.selectinload(PurchaseRecord.payment_account),
                    db.selectinload(PurchaseRecord.deposit_account),
                    db.selectinload(PurchaseRecord.operator)
                )
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(10)
            )
            .all()
        )"""
    
    content = content.replace(old_buyin_query, new_buyin_query)
    
    # 寫入修改後的文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已創建臨時修復")
    print("📁 原文件已備份為 app.py.backup")
    print("⚠️  這只是臨時解決方案，請盡快修復資料庫")

if __name__ == "__main__":
    create_temp_fix()



