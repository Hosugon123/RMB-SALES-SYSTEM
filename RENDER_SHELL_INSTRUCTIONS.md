# Render Shell 執行指南（無需複製貼上）

## 🎯 方法 1：使用 Git 同步（推薦）

### 步驟 1：本地提交並推送

```bash
# 在本地執行
git add verify_sales_and_settlements.py
git commit -m "Add sales verification script"
git push
```

### 步驟 2：在 Render Shell 中拉取

```bash
cd ~/project/src
git pull
python verify_sales_and_settlements.py
```

---

## 🎯 方法 2：直接在 Shell 中執行 Python 代碼

### 一次性執行（複製整個命令）

在 Render Shell 中執行以下**單行命令**：

```bash
cd ~/project/src && python -c "
import sys, os
sys.path.insert(0, '.')
from app import app, db, SalesRecord, LedgerEntry, Customer, CashAccount
with app.app_context():
    # 總售出
    sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    total_sales_rmb = sum(s.rmb_amount for s in sales)
    total_sales_twd = sum(s.twd_amount for s in sales)
    # 總銷帳
    settlements = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == 'SETTLEMENT')).scalars().all()
    total_settlements = sum(s.amount for s in settlements)
    # 應收帳款
    customers = db.session.execute(db.select(Customer)).scalars().all()
    total_receivables_db = sum(c.total_receivables_twd for c in customers)
    calculated_receivables = total_sales_twd - total_settlements
    # WITHDRAW
    withdraws = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == 'WITHDRAW').filter(LedgerEntry.description.like('%售出扣款%'))).scalars().all()
    total_withdraw_rmb = sum(abs(r.amount) for r in withdraws)
    # 輸出
    print('='*80)
    print('數據驗證報告')
    print('='*80)
    print(f'1. 歷史總售出: {total_sales_twd:,.2f} TWD ({total_sales_rmb:,.2f} RMB)')
    print(f'2. 歷史總銷帳: {total_settlements:,.2f} TWD')
    print(f'3. 應收帳款（計算）: {calculated_receivables:,.2f} TWD')
    print(f'4. 應收帳款（資料庫）: {total_receivables_db:,.2f} TWD')
    print(f'5. 售出扣款 WITHDRAW: {total_withdraw_rmb:,.2f} RMB ({len(withdraws)} 筆)')
    print(f'6. WITHDRAW/總售出: {total_withdraw_rmb/total_sales_rmb*100 if total_sales_rmb > 0 else 0:.2f}%')
    print('='*80)
"
```

---

## 🎯 方法 3：創建簡化腳本文件（使用 echo）

在 Render Shell 中逐行執行：

```bash
cd ~/project/src

# 創建腳本
cat > verify_quick.py << 'ENDOFFILE'
import sys, os
sys.path.insert(0, '.')
from app import app, db, SalesRecord, LedgerEntry, Customer, CashAccount

with app.app_context():
    sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    total_sales_rmb = sum(s.rmb_amount for s in sales)
    total_sales_twd = sum(s.twd_amount for s in sales)
    
    settlements = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == 'SETTLEMENT')).scalars().all()
    total_settlements = sum(s.amount for s in settlements)
    
    customers = db.session.execute(db.select(Customer)).scalars().all()
    total_receivables_db = sum(c.total_receivables_twd for c in customers)
    calculated_receivables = total_sales_twd - total_settlements
    
    withdraws = db.session.execute(db.select(LedgerEntry).filter(LedgerEntry.entry_type == 'WITHDRAW').filter(LedgerEntry.description.like('%售出扣款%'))).scalars().all()
    total_withdraw_rmb = sum(abs(r.amount) for r in withdraws)
    
    print('='*80)
    print('數據驗證報告')
    print('='*80)
    print(f'1. 歷史總售出: {total_sales_twd:,.2f} TWD ({total_sales_rmb:,.2f} RMB)')
    print(f'2. 歷史總銷帳: {total_settlements:,.2f} TWD')
    print(f'3. 應收帳款（計算）: {calculated_receivables:,.2f} TWD')
    print(f'4. 應收帳款（資料庫）: {total_receivables_db:,.2f} TWD')
    print(f'5. 售出扣款 WITHDRAW: {total_withdraw_rmb:,.2f} RMB ({len(withdraws)} 筆)')
    ratio = total_withdraw_rmb/total_sales_rmb*100 if total_sales_rmb > 0 else 0
    print(f'6. WITHDRAW/總售出比例: {ratio:.2f}%')
    print('='*80)
ENDOFFILE

# 執行
python verify_quick.py
```

---

## 🎯 方法 4：檢查是否已有文件

在 Render Shell 中先檢查：

```bash
cd ~/project/src
ls -la verify_sales_and_settlements.py
```

如果文件已經存在（可能從之前的 Git pull），直接執行：

```bash
python verify_sales_and_settlements.py
```

---

## 💡 推薦順序

1. **先試方法 4**：檢查文件是否已存在
2. **如果沒有，用方法 1**：Git 推送和拉取（最可靠）
3. **如果 Git 不可用，用方法 2**：單行 Python 命令（最快速）
4. **如果都不行，用方法 3**：在 Shell 中創建簡化腳本

---

## 📊 輸出說明

執行後會看到：
- **歷史總售出**：所有銷售記錄的總額（RMB 和 TWD）
- **歷史總銷帳**：所有銷帳記錄的總額
- **應收帳款**：計算值 vs 資料庫值
- **售出扣款 WITHDRAW**：這就是您看到的「總扣款金額」
- **比例**：WITHDRAW 佔總售出的百分比

這樣您就能立即看到所有數據的關係了！


