# Render Shell 備份 WITHDRAW 記錄（已修復）

## ✅ 修復後的備份命令

直接在 Render Shell 中執行以下命令：

```bash
cd ~/project/src && python -c "
import sys, os, json
from datetime import datetime
sys.path.insert(0, '.')
from app import app, db, LedgerEntry

with app.app_context():
    records = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type=='WITHDRAW').filter(LedgerEntry.description.like('%售出扣款%'))).scalars().all()
    data = [{'id': r.id, 'account_id': r.account_id, 'account_name': r.account.name if r.account else None, 'amount': float(r.amount), 'description': r.description, 'entry_date': r.entry_date.isoformat() if r.entry_date else None, 'operator_id': r.operator_id} for r in records]
    fname = f'withdraw_backup_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'backup_date': datetime.now().isoformat(), 'total_records': len(data), 'records': data}, f, ensure_ascii=False, indent=2)
    print(f'✅ 備份完成: {fname} ({len(data)} 筆記錄)')
"
```

## 🎯 執行步驟

### 步驟 1：備份（已修復）
直接複製上面的命令到 Render Shell 執行

### 步驟 2：清理 WITHDRAW 記錄
執行清理腳本（如果文件已存在）：

```bash
python cleanup_withdraw_no_change.py
```

或者使用一行命令（如果文件不存在）：

```bash
cd ~/project/src && python -c "
import sys
sys.path.insert(0, '.')
from app import app, db, LedgerEntry, CashAccount, SalesRecord

with app.app_context():
    # 查找所有售出扣款 WITHDRAW 記錄
    withdraw_records = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type=='WITHDRAW').filter(LedgerEntry.description.like('%售出扣款%'))).scalars().all()
    print(f'找到 {len(withdraw_records)} 筆 WITHDRAW 記錄')
    
    # 查找 0107 帳戶
    account_0107 = db.session.execute(db.select(CashAccount).filter(CashAccount.id==27)).scalar_one()
    sales_0107 = db.session.execute(db.select(SalesRecord).filter(SalesRecord.rmb_account_id==27)).scalars().all()
    withdraw_total_0107 = sum(abs(r.amount) for r in withdraw_records if r.account_id==27)
    sales_total_0107 = sum(s.rmb_amount for s in sales_0107)
    adjustment = withdraw_total_0107 - sales_total_0107
    
    print(f'0107 支付寶: 當前餘額 {account_0107.balance:,.2f}, 將調整 +{adjustment:,.2f}')
    print(f'將刪除 {len(withdraw_records)} 筆 WITHDRAW 記錄')
    
    response = input('是否繼續？(yes/no): ')
    if response.lower() == 'yes':
        account_0107.balance += adjustment
        for r in withdraw_records:
            db.session.delete(r)
        db.session.commit()
        print(f'✅ 清理完成！0107 餘額: {account_0107.balance:,.2f}')
    else:
        print('❌ 已取消')
"
```

---

## ⚠️ 注意事項

1. **備份文件會保存在 `~/project/src/` 目錄**
2. **備份文件名格式**：`withdraw_backup_YYYYMMDD_HHMMSS.json`
3. **備份包含**：記錄 ID、帳戶信息、金額、描述、日期等

