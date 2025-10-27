#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查銷帳記錄"""

from app import app, db
from app import LedgerEntry

with app.app_context():
    # 查找客戶"許討厭"
    from app import Customer
    customer = Customer.query.filter_by(name='許討厭').first()
    
    if not customer:
        print('❌ 找不到客戶「許討厭」')
        exit(1)
    
    print(f'\n📋 客戶: {customer.name} (ID: {customer.id})')
    
    # 查詢所有銷帳記錄
    settlement_entries = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "SETTLEMENT")
        .filter(LedgerEntry.description.like(f"%{customer.name}%"))
        .order_by(LedgerEntry.entry_date.asc())
    ).scalars().all()
    
    print(f'\n🔍 找到 {len(settlement_entries)} 筆銷帳記錄 (LedgerEntry)')
    
    if len(settlement_entries) == 0:
        print('⚠️  沒有找到銷帳記錄！這就是問題所在。')
    else:
        print('\n📋 銷帳記錄明細:')
        for entry in settlement_entries:
            print(f'   日期: {entry.entry_date}, 金額: NT$ {entry.amount:,.2f}, 描述: {entry.description}')

