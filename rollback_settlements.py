#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
緊急回滾腳本：將所有 SalesRecord 重置為未結清狀態
"""

from app import app, db
from models import SalesRecord, Customer
from sqlalchemy import func

def rollback_all_settlements():
    """將所有銷售記錄重置為未結清狀態"""
    with app.app_context():
        print('🔄 開始回滾操作...')
        print('⚠️  將所有 SalesRecord 的 is_settled 設置為 False\n')
        
        # 查詢所有銷售記錄
        all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        print(f'📊 找到 {len(all_sales)} 筆銷售記錄')
        
        # 統計當前已結清的記錄數
        settled_count = sum(1 for sale in all_sales if sale.is_settled)
        print(f'📊 其中 {settled_count} 筆已標記為已結清\n')
        
        # 將所有記錄設置為未結清
        for sale in all_sales:
            sale.is_settled = False
        
        db.session.commit()
        print('✅ 回滾完成！所有銷售記錄已重置為未結清狀態\n')
        
        # 顯示每個客戶的銷售記錄總額
        print('📋 各客戶銷售記錄總額（重置後）:')
        customers = db.session.execute(db.select(Customer)).scalars().all()
        for customer in customers:
            total = db.session.execute(
                db.select(func.sum(SalesRecord.twd_amount))
                .filter(SalesRecord.customer_id == customer.id)
            ).scalar() or 0.0
            if total > 0:
                print(f'   {customer.name}: NT$ {total:,.2f}')
        
        print('\n✅ 回滾操作完成！')
        print('🔄 現在請執行 "flask fix-historical-settlements" 重新修復（只執行一次！）')

if __name__ == '__main__':
    rollback_all_settlements()

