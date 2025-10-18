# 單個帳戶餘額變化明細功能

## 功能概述

本功能增強了交易紀錄的顯示，新增了「出款戶餘額變化」和「入款戶餘額變化」兩個欄位，讓用戶能夠清楚看到每筆交易對具體帳戶餘額的影響，而不是系統總體餘額的變化。

## 主要改進

### 1. 後端API增強 (`app.py`)

在 `/api/cash_management/transactions` API中新增了單個帳戶餘額變化的追蹤邏輯：

#### A. 帳戶餘額追蹤系統
```python
# 計算每個帳戶的餘額變化追蹤
# 建立帳戶餘額追蹤字典
account_balances = {}

# 獲取所有帳戶的初始餘額
all_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
for account in all_accounts:
    account_balances[account.id] = {
        'name': account.name,
        'currency': account.currency,
        'current_balance': account.balance
    }
```

#### B. 交易記錄增強
為每筆交易記錄新增了帳戶ID信息：
- `payment_account_id`: 出款帳戶ID
- `deposit_account_id`: 入款帳戶ID
- `account_balance_changes`: 帳戶餘額變化詳情

#### C. 餘額變化計算
```python
# 從最早的記錄開始計算每個帳戶的餘額變化
chronological_stream = sorted(unified_stream, key=lambda x: x["date"])

for record in chronological_stream:
    # 初始化出帳前後餘額記錄
    record["account_balance_changes"] = {}
    
    # 根據交易類型確定影響的帳戶
    payment_account_id = record.get("payment_account_id")
    deposit_account_id = record.get("deposit_account_id")
    
    # 記錄出帳前餘額並計算變動
    # ... 詳細的餘額變化計算邏輯
```

### 2. 前端顯示優化 (`templates/cash_management.html`)

#### A. 表格結構更新
- 將原本的「出帳前餘額」和「出帳後餘額」欄位改為「出款戶餘額變化」和「入款戶餘額變化」
- 每個欄位顯示具體帳戶的餘額變化詳情

#### B. JavaScript渲染邏輯
```javascript
// 出款戶餘額變化顯示
let paymentAccountBalanceHtml = '-';
if (m.account_balance_changes && m.payment_account_id && m.account_balance_changes[m.payment_account_id]) {
    const paymentAccount = m.account_balance_changes[m.payment_account_id];
    const changeAmount = paymentAccount.change || 0;
    const balanceBefore = paymentAccount.balance_before || 0;
    const balanceAfter = paymentAccount.balance_after || 0;
    
    paymentAccountBalanceHtml = '<div class="small account-balance-change">' +
        '<div class="fw-bold text-primary border-bottom border-primary pb-1 mb-1">' + paymentAccount.account_name + '</div>' +
        '<div class="text-secondary small">前: ' + balanceBefore.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="' + changeClass + ' small">變動: ' + (changeAmount > 0 ? '+' : '') + changeAmount.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-dark small">後: ' + balanceAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
}
```

#### C. CSS樣式優化
```css
/* 帳戶餘額變化列的樣式 */
.account-balance-change {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 6px;
    padding: 8px;
    border-left: 3px solid #6c757d;
    min-width: 120px;
}

.account-balance-change .fw-bold {
    font-size: 0.85rem;
    margin-bottom: 4px;
}

.account-balance-change .small {
    font-size: 0.75rem;
    line-height: 1.2;
    margin-bottom: 2px;
}
```

## 數據結構

每筆交易記錄現在包含以下帳戶餘額變化信息：

```json
{
    "payment_account_id": 1,
    "deposit_account_id": 2,
    "account_balance_changes": {
        "1": {
            "account_name": "7773台新",
            "currency": "TWD",
            "balance_before": 1483126.079,
            "balance_after": 1583126.079,
            "change": 100000.00
        },
        "2": {
            "account_name": "6186現",
            "currency": "TWD", 
            "balance_before": 1383126.079,
            "balance_after": 1483126.079,
            "change": 100000.00
        }
    }
}
```

## 視覺效果

### 出款戶餘額變化
- 藍色標題邊框
- 顯示帳戶名稱
- 出帳前餘額（灰色）
- 變動金額（綠色/紅色）
- 出帳後餘額（深色）

### 入款戶餘額變化
- 綠色標題邊框
- 顯示帳戶名稱
- 入帳前餘額（灰色）
- 變動金額（綠色/紅色）
- 入帳後餘額（深色）

## 功能特點

1. **具體帳戶追蹤**: 顯示每個具體帳戶的餘額變化，而不是系統總體餘額
2. **詳細變化信息**: 包含帳戶名稱、出帳前餘額、變動金額、出帳後餘額
3. **視覺化區分**: 使用不同顏色和樣式來區分出款戶和入款戶
4. **金額格式化**: 使用千分位分隔符，保留兩位小數
5. **響應式設計**: 表格支援橫向滾動，適應不同螢幕尺寸

## 使用說明

1. 進入現金管理頁面
2. 查看「近期交易記錄」表格
3. 現在可以看到每筆交易的：
   - 出款戶餘額變化（藍色邊框）
   - 入款戶餘額變化（綠色邊框）
   - 每個具體帳戶的詳細餘額變化

## 技術細節

- 後端計算順序：從最早的交易開始，按時間順序追蹤每個帳戶的餘額變化
- 前端顯示順序：最新的交易顯示在最上方
- 帳戶識別：通過帳戶ID精確追蹤每個帳戶的變化
- 數據完整性：包含帳戶名稱、貨幣類型、餘額變化等完整信息

## 測試

創建了測試頁面 `test_account_specific_balance.html` 來驗證功能的正確性，包含：
- 模擬交易數據（包含帳戶餘額變化信息）
- 完整的表格顯示
- 樣式效果展示

## 與之前版本的差異

| 項目 | 之前版本 | 新版本 |
|------|----------|--------|
| 餘額顯示 | 系統總體餘額變化 | 具體帳戶餘額變化 |
| 信息詳度 | 累積餘額 | 帳戶名稱 + 前後餘額 + 變動金額 |
| 視覺區分 | 單一顏色 | 出款戶(藍色) vs 入款戶(綠色) |
| 實用性 | 總體概覽 | 具體帳戶明細追蹤 |
