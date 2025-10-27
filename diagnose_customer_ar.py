#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""診斷客戶應收帳款問題"""

from app import app, db, Customer
from sqlalchemy import func

with app.app_context():
    # 查找客戶"許討厭"
    customer = Customer.query.filter_by(name='許討厭').first()
    
    if not customer:
        print('❌ 找不到客戶「許討厭」')
        exit(1)
    
    print(f'\n📋 客戶: {customer.name} (ID: {customer.id})')
    print(f'📊 Customer.total_receivables_twd: NT$ {customer.total_receivables_twd:,.2f}\n')
    
    # 查詢所有未結清的銷售記錄
    from app import SalesRecord
    
    unsettled_sales = db.session.execute(
        db.select(SalesRecord)
        .filter(SalesRecord.customer_id == customer.id)
        .filter(SalesRecord.is_settled == False)
        .order_by(SalesRecord.created_at.asc())
    ).scalars().all()
    
    print(f'📊 未結清訂單數: {len(unsettled_sales)}')
    
    total_unsettled = sum(sale.twd_amount for sale in unsettled_sales)
    print(f'📊 未結清訂單總額 (計算): NT$ {total_unsettled:,.2f}\n')
    
    print('📋 未結清訂單明細:')
    for sale in unsettled_sales:
        print(f'   ID {sale.id}: NT$ {sale.twd_amount:,.2f} (日期: {sale.created_at})')
    
    # 查詢所有已結清的銷售記錄
    settled_sales = db.session.execute(
        db.select(SalesRecord)
        .filter(SalesRecord.customer_id == customer.id)
        .filter(SalesRecord.is_settled == True)
        .order_by(SalesRecord.created_at.asc())
    ).scalars().all()
    
    print(f'\n✅ 已結清訂單數: {len(settled_sales)}')
    
    total_settled = sum(sale.twd_amount for sale in settled_sales)
    print(f'✅ 已結清訂單總額: NT$ {total_settled:,.2f}\n')
    
    print('✅ 已結清訂單明細:')
    for sale in settled_sales:
        print(f'   ID {sale.id}: NT$ {sale.twd_amount:,.2f} (日期: {sale.created_at})')
    
    # 計算期望值
    print(f'\n📊 期望應收帳款 (未結清總額): NT$ {total_unsettled:,.2f}')
    print(f'📊 實際 Customer.total_receivables_twd: NT$ {customer.total_receivables_twd:,.2f}')
    print(f'📊 差異: NT$ {customer.total_receivables_twd - total_unsettled:,.2f}')
    
    if abs(customer.total_receivables_twd - total_unsettled) < 0.01:
        print('\n✅ 數據一致！問題可能在前端顯示邏輯。')
    else:
        print('\n❌ 數據不一致！需要執行 flask rebuild-customer-ar。')

