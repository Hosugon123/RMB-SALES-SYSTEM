#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速回滾：重置所有銷售記錄為未結清狀態"""

from app import app, db
from models import SalesRecord

with app.app_context():
    print('🔄 開始回滾操作...')
    
    # 重置所有銷售記錄
    all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    settled_count = sum(1 for sale in all_sales if sale.is_settled)
    
    print(f'📊 找到 {len(all_sales)} 筆銷售記錄，其中 {settled_count} 筆已標記為已結清')
    
    for sale in all_sales:
        sale.is_settled = False
    
    db.session.commit()
    
    print(f'✅ 回滾完成！所有 {len(all_sales)} 筆記錄已重置為未結清狀態')
    print('🔄 現在可以安全地重新執行 "flask fix-historical-settlements --reset"')

