#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
備份 WITHDRAW 記錄到 JSON 文件

在執行清理前，建議先備份這些記錄
"""

import sys
import os
import json
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import app, db, LedgerEntry

def backup_withdraw_records():
    """備份所有售出扣款 WITHDRAW 記錄到 JSON"""
    print("=" * 80)
    print("備份 WITHDRAW 記錄")
    print("=" * 80)
    
    with app.app_context():
        try:
            # 查找所有售出扣款 WITHDRAW 記錄
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
            ).scalars().all()
            
            if len(withdraw_records) == 0:
                print("✅ 沒有找到需要備份的 WITHDRAW 記錄")
                return 0
            
            print(f"\n找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
            
            # 轉換為字典列表
            records_data = []
            for record in withdraw_records:
                records_data.append({
                    'id': record.id,
                    'account_id': record.account_id,
                    'account_name': record.account.name if record.account else None,
                    'amount': float(record.amount),
                    'description': record.description,
                    'entry_date': record.entry_date.isoformat() if record.entry_date else None,
                    'created_at': record.created_at.isoformat() if record.created_at else None,
                })
            
            # 生成備份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"withdraw_records_backup_{timestamp}.json"
            
            # 保存到文件
            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'total_records': len(records_data),
                'records': records_data
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 備份完成！")
            print(f"   備份文件: {backup_file}")
            print(f"   記錄數量: {len(records_data)} 筆")
            print(f"   文件大小: {os.path.getsize(backup_file) / 1024:.2f} KB")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ 備份失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    print("備份 WITHDRAW 記錄工具")
    print("在執行清理前，建議先備份這些記錄\n")
    
    exit_code = backup_withdraw_records()
    sys.exit(exit_code)

