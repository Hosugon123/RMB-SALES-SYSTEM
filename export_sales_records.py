#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
導出所有銷售記錄到 CSV 文件
用於創建資料庫快照
"""

from app import app, db
from datetime import datetime
import csv

def export_sales_records():
    """導出所有銷售記錄到 CSV"""
    with app.app_context():
        # 查詢所有銷售記錄
        from app import SalesRecord
        
        all_sales = db.session.execute(
            db.select(SalesRecord).order_by(SalesRecord.created_at.desc())
        ).scalars().all()
        
        print(f'📊 找到 {len(all_sales)} 筆銷售記錄')
        
        # 創建 CSV 文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'sales_records_backup_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'customer_id', 'rmb_account_id', 'operator_id', 
                'rmb_amount', 'exchange_rate', 'twd_amount', 
                'is_settled', 'created_at', 'customer_name'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for sale in all_sales:
                # 獲取客戶名稱
                customer_name = sale.customer.name if sale.customer else 'N/A'
                
                writer.writerow({
                    'id': sale.id,
                    'customer_id': sale.customer_id,
                    'rmb_account_id': sale.rmb_account_id,
                    'operator_id': sale.operator_id,
                    'rmb_amount': str(sale.rmb_amount),
                    'exchange_rate': str(sale.exchange_rate),
                    'twd_amount': str(sale.twd_amount),
                    'is_settled': sale.is_settled,
                    'created_at': sale.created_at.isoformat() if sale.created_at else '',
                    'customer_name': customer_name
                })
        
        print(f'✅ 已導出到: {filename}')
        print(f'📁 檔案包含所有銷售記錄，可用於恢復')
        
        # 顯示各客戶的記錄數
        from collections import Counter
        customer_counts = Counter(
            sale.customer.name if sale.customer else 'N/A' 
            for sale in all_sales
        )
        
        print('\n📋 各客戶銷售記錄數:')
        for customer_name, count in customer_counts.most_common():
            print(f'   {customer_name}: {count} 筆')

if __name__ == '__main__':
    export_sales_records()

