# Render Shell 備份 WITHDRAW 記錄指南

## 🔧 問題：文件不存在

如果執行 `python backup_withdraw_records.py` 時提示文件不存在，可能是：
1. Render 還沒拉取最新代碼
2. 需要在 Render 中重新部署

## ✅ 解決方案

### 方案 1：拉取最新代碼（推薦）

在 Render Shell 中執行：

```bash
cd ~/project/src
git pull origin main
python backup_withdraw_records.py
```

### 方案 2：直接在 Shell 中創建腳本

如果 Git pull 失敗，可以直接在 Shell 中創建腳本：

```bash
cd ~/project/src

# 創建備份腳本
cat > backup_withdraw_records.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import json
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import app, db, LedgerEntry

with app.app_context():
    try:
        withdraw_records = db.session.execute(
            db.select(LedgerEntry)
            .filter(LedgerEntry.entry_type == "WITHDRAW")
            .filter(LedgerEntry.description.like("%售出扣款%"))
        ).scalars().all()
        
        if len(withdraw_records) == 0:
            print("✅ 沒有找到需要備份的 WITHDRAW 記錄")
            exit(0)
        
        print(f"找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
        
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"withdraw_records_backup_{timestamp}.json"
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'total_records': len(records_data),
            'records': records_data
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 備份完成！")
        print(f"   備份文件: {backup_file}")
        print(f"   記錄數量: {len(records_data)} 筆")
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
EOF

# 執行備份
python backup_withdraw_records.py
```

### 方案 3：一行命令備份（最簡單）

直接執行以下 Python 代碼：

```bash
cd ~/project/src && python -c "
import sys, os, json
from datetime import datetime
sys.path.insert(0, '.')
from app import app, db, LedgerEntry

with app.app_context():
    records = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type=='WITHDRAW').filter(LedgerEntry.description.like('%售出扣款%'))).scalars().all()
    data = [{'id': r.id, 'account_id': r.account_id, 'account_name': r.account.name if r.account else None, 'amount': float(r.amount), 'description': r.description, 'entry_date': r.entry_date.isoformat() if r.entry_date else None, 'created_at': r.created_at.isoformat() if r.created_at else None} for r in records]
    fname = f'withdraw_backup_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'backup_date': datetime.now().isoformat(), 'total_records': len(data), 'records': data}, f, ensure_ascii=False, indent=2)
    print(f'✅ 備份完成: {fname} ({len(data)} 筆記錄)')
"
```

---

## 🎯 推薦流程

1. **先嘗試拉取代碼**：
   ```bash
   cd ~/project/src
   git pull origin main
   ```

2. **如果成功，直接執行**：
   ```bash
   python backup_withdraw_records.py
   ```

3. **如果 Git pull 失敗，使用方案 3 的一行命令**

4. **備份完成後，執行清理**：
   ```bash
   python cleanup_withdraw_no_change.py
   ```

