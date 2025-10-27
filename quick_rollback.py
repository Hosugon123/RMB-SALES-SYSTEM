#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速回滾：重置所有銷售記錄為未結清狀態"""

from app import app, db

with app.app_context():
    print('🔄 開始回滾操作...')
    
    # 使用原始 SQL 直接更新
    result = db.session.execute(
        "UPDATE sales_records SET is_settled = FALSE"
    )
    db.session.commit()
    
    print(f'✅ 回滾完成！已重置所有銷售記錄為未結清狀態')
    print('🔄 現在可以安全地重新執行 "flask fix-historical-settlements --reset"')

