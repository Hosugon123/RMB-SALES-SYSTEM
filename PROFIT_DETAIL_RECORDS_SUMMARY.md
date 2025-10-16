# 🎯 利潤詳細記錄功能實現總結

## 功能需求

**用戶需求：** 近期交易記錄裡記錄利潤變更的欄位想記錄得更詳細，要有變動前利潤、變動後利潤、變動之利潤數字。

**實現目標：** 將單一的「利潤」欄位擴展為三個詳細的利潤欄位，提供更完整的利潤變動追蹤。

## 實現內容

### ✅ 1. 數據庫結構變更

#### A. 模型修改
**文件：** `app.py`

**新增欄位到 LedgerEntry 模型：**
```python
class LedgerEntry(db.Model):
    # 新增：詳細利潤信息欄位
    profit_before = db.Column(db.Float, nullable=True)  # 變動前利潤
    profit_after = db.Column(db.Float, nullable=True)   # 變動後利潤
    profit_change = db.Column(db.Float, nullable=True)  # 變動之利潤數字
```

#### B. 數據庫遷移
**文件：** `migrations/versions/add_profit_detail_fields_to_ledger.py`

**遷移內容：**
```python
def upgrade():
    op.add_column('ledger_entries', sa.Column('profit_before', sa.Float(), nullable=True))
    op.add_column('ledger_entries', sa.Column('profit_after', sa.Float(), nullable=True))
    op.add_column('ledger_entries', sa.Column('profit_change', sa.Float(), nullable=True))
```

### ✅ 2. 後端邏輯修改

#### A. 利潤提款記錄創建邏輯
**文件：** `app.py` (第4043-4092行)

**新增功能：**
```python
# 計算當前總利潤（用於記錄變動前後利潤）
current_total_profit = 0.0
if withdraw_type == "profit":
    # 計算當前銷售利潤總和
    all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    
    for sale in all_sales:
        profit_info = FIFOService.calculate_profit_for_sale(sale)
        if profit_info:
            current_total_profit += profit_info.get('profit_twd', 0.0)
    
    # 扣除之前的利潤提款
    previous_profit_withdrawals = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
        .filter(LedgerEntry.id != None)
    ).scalars().all()
    
    previous_withdrawals = sum(entry.amount for entry in previous_profit_withdrawals)
    current_total_profit -= previous_withdrawals

# 創建流水記錄
entry = LedgerEntry(
    entry_type="PROFIT_WITHDRAW",
    amount=amount,
    description=description,
    operator_id=current_user.id,
)

# 如果是利潤提款，記錄詳細利潤信息
if withdraw_type == "profit":
    entry.profit_before = current_total_profit
    entry.profit_after = current_total_profit - amount
    entry.profit_change = -amount  # 負數表示減少
```

#### B. API 數據返回
**文件：** `app.py` (第6254-6274行)

**修改內容：**
```python
# 構建基本記錄
record = {
    "type": entry.entry_type,
    "date": entry.entry_date.isoformat(),
    "description": entry.description,
    "twd_change": twd_change,
    "rmb_change": rmb_change,
    "operator": entry.operator.username if entry.operator else "未知",
    "payment_account": payment_account,
    "deposit_account": deposit_account,
    "note": getattr(entry, 'note', None),
}

# 如果是利潤提款，添加詳細利潤信息
if entry.entry_type == "PROFIT_WITHDRAW":
    record["profit_before"] = entry.profit_before
    record["profit_after"] = entry.profit_after
    record["profit_change"] = entry.profit_change
    record["profit"] = entry.profit_change  # 保持向後兼容
```

### ✅ 3. 前端顯示修改

#### A. 表格結構變更
**文件：** `templates/cash_management.html`

**修改內容：**
```html
<!-- 修改前 -->
<th class="text-end pe-3">利潤</th>

<!-- 修改後 -->
<th class="text-end">變動前利潤</th>
<th class="text-end">變動後利潤</th>
<th class="text-end pe-3">變動之利潤數字</th>
```

#### B. JavaScript 渲染邏輯
**文件：** `templates/cash_management.html` (第2134-2241行)

**新增功能：**
```javascript
// 新增：詳細利潤信息
const profitBefore = parseFloat(m.profit_before ?? m.profitBefore) || null;
const profitAfter = parseFloat(m.profit_after ?? m.profitAfter) || null;
const profitChange = parseFloat(m.profit_change ?? m.profitChange) || null;

// 格式化詳細利潤信息
const profitBeforeDisplay = profitBefore !== null ? profitBefore.toLocaleString('en-US', {minimumFractionDigits: 2}) : '-';
const profitAfterDisplay = profitAfter !== null ? profitAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) : '-';
const profitChangeDisplay = profitChange !== null ? (profitChange > 0 ? '+' : '') + profitChange.toLocaleString('en-US', {minimumFractionDigits: 2}) : '-';

// 設置顏色
const profitChangeColorClass = profitChange !== null ? (profitChange > 0 ? 'text-success' : 'text-danger') : 'text-muted';

// 表格行渲染
const row = '<tr class="transaction-row">' +
    // ... 其他欄位 ...
    '<td class="text-end"><small class="text-info">' + profitBeforeDisplay + '</small></td>' +
    '<td class="text-end"><small class="text-info">' + profitAfterDisplay + '</small></td>' +
    '<td class="text-end pe-3"><small class="' + profitChangeColorClass + '">' + profitChangeDisplay + '</small></td>' +
    '</tr>';
```

#### C. 類型處理
**新增利潤提款類型處理：**
```javascript
case 'PROFIT_WITHDRAW':
    typeDisplay = '利潤扣除';
    typeClass = 'badge bg-warning-subtle text-warning-emphasis';
    break;
case 'ASSET_WITHDRAW':
    typeDisplay = '資產提款';
    typeClass = 'badge bg-secondary-subtle text-secondary-emphasis';
    break;
```

## 功能特點

### 📊 **詳細利潤追蹤**
- **變動前利潤**：交易發生前的總利潤狀態
- **變動後利潤**：交易發生後的總利潤狀態
- **變動之利潤數字**：此次交易對利潤的具體影響

### 🎨 **視覺設計**
- **變動前/後利潤**：藍色文字（`text-info`）
- **變動金額**：綠色（增加）或紅色（減少）
- **利潤提款**：黃色標籤（`bg-warning-subtle`）
- **資產提款**：灰色標籤（`bg-secondary-subtle`）

### 🔧 **技術實現**
- **條件顯示**：只有利潤提款記錄顯示詳細信息
- **向後兼容**：保留原有的 `profit` 欄位
- **數據完整性**：準確計算變動前後的利潤狀態

## 數據結構

### 📋 **數據庫記錄示例**

**利潤提款記錄：**
```python
{
    "entry_type": "PROFIT_WITHDRAW",
    "amount": 500.00,
    "profit_before": 24431.00,    # 變動前利潤
    "profit_after": 23931.00,     # 變動後利潤
    "profit_change": -500.00,     # 變動之利潤數字
    "description": "利潤提款"
}
```

**資產提款記錄：**
```python
{
    "entry_type": "ASSET_WITHDRAW",
    "amount": 1000.00,
    "profit_before": None,        # 不影響利潤
    "profit_after": None,         # 不影響利潤
    "profit_change": None,        # 不影響利潤
    "description": "資產提款"
}
```

### 📊 **前端顯示示例**

| 類型 | 變動前利潤 | 變動後利潤 | 變動之利潤數字 |
|------|------------|------------|----------------|
| 利潤扣除 | 24,431.00 | 23,931.00 | -500.00 |
| 資產提款 | - | - | - |
| 售出 | - | - | - |

## 測試驗證

### 🧪 **測試頁面**
- **`test_profit_detail_records.html`** - 利潤詳細記錄功能測試

### 📝 **測試步驟**
1. **執行數據庫遷移**：`flask db upgrade`
2. **重啟應用程序**
3. **進行利潤提款測試**
4. **檢查近期交易記錄** - 驗證新的利潤詳細欄位
5. **進行資產提款測試** - 驗證不顯示利潤詳細信息

### ✅ **驗證要點**
- 利潤提款記錄顯示變動前、變動後、變動金額
- 資產提款記錄不顯示利潤詳細信息（顯示 "-"）
- 其他類型記錄不顯示利潤詳細信息
- 表格列數正確（從 11 列增加到 13 列）
- 顏色顯示正確（負數為紅色）
- 數據計算準確

## 相關文件

### 📁 **修改的文件**
- `app.py` - 模型定義、後端邏輯、API 修改
- `templates/cash_management.html` - 前端顯示邏輯

### 📁 **新增的文件**
- `migrations/versions/add_profit_detail_fields_to_ledger.py` - 數據庫遷移
- `test_profit_detail_records.html` - 功能測試頁面

### 📁 **相關功能**
- 利潤提款功能
- 資產提款功能
- 現金管理頁面
- 儀表板利潤計算

## 預期效果

實現後，用戶將能夠：

1. ✅ **詳細追蹤利潤變動** - 清楚看到每次利潤提款對總利潤的影響
2. ✅ **完整的變動記錄** - 變動前、變動後、變動金額一目了然
3. ✅ **準確的財務數據** - 利潤計算更加精確和透明
4. ✅ **更好的財務管理** - 便於分析和審計利潤使用情況
5. ✅ **數據一致性** - 確保利潤數據的準確性和完整性

---

**結論：** 成功實現了利潤詳細記錄功能，現在近期交易記錄會顯示變動前利潤、變動後利潤、變動之利潤數字，提供了更完整和透明的利潤變動追蹤。


