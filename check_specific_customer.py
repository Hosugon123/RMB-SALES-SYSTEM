#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查特定客戶的詳細情況"""

from app import app, db, Customer

with app.app_context():
    customer = Customer.query.filter_by(name='許討厭').first()
    
    # 查詢所有未結清記錄
    from app import SalesRecord
    unsettled = SalesRecord.query.filter_by(customer_id=customer.id, is_settled=False).all()
    
    print(f'\n📋 客戶: {customer.name}')
    print(f'📊 Customer.total_receivables_twd: NT$ {customer.total_receivables_twd:,.2f}')
    print(f'\n📊 未結清訂單數: {len(unsettled)}')
    
    for s in unsettled:
        print(f'   ID {s.id}: NT$ {s.twd_amount:,.2f}, is_settled={s.is_settled}, 日期: {s.created_at}')
    
    # 查詢所有已結清記錄
    settled = SalesRecord.query.filter_by(customer_id=customer.id, is_settled=True).all()
    print(f'\n📊 已結清訂單數: {len(settled)}')
    
    for s in settled:
        print(f'   ID {s.id}: NT$ {s.twd_amount:,.2f}, is_settled={s.is_settled}, 日期: {s.created_at}')

