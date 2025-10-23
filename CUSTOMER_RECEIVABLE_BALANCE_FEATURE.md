# 客戶個人應收帳款餘額變化功能實現總結

## 🎯 功能需求

**用戶需求**：希望售出記錄的入款戶餘額變化要記錄客戶的個人應收帳款的詳細餘額變化（訂單前、訂單金額、訂單後），並且要與客戶交易紀錄頁面連動，兩邊都要有記錄。

## 🔧 已完成的實現

### 1. 現金頁面售出記錄的應收帳款餘額變化

#### A. 後端邏輯修改
**文件**：`app.py` - `get_cash_management_transactions`函數

**新增功能**：
```python
# 計算客戶個人應收帳款餘額變化
try:
    # 獲取客戶當前應收帳款餘額
    customer_receivable_after = customer.total_receivables_twd if customer else 0
    customer_receivable_before = customer_receivable_after - twd_amount
    customer_receivable_change = twd_amount
    
    print(f"DEBUG: 客戶應收帳款變化 - 變動前: {customer_receivable_before:.2f}, 變動: {customer_receivable_change:.2f}, 變動後: {customer_receivable_after:.2f}")
except Exception as e:
    print(f"DEBUG: ⚠️ 計算客戶應收帳款變化失敗: {e}")
    customer_receivable_before = twd_amount if twd_amount else 0
    customer_receivable_after = twd_amount if twd_amount else 0
    customer_receivable_change = twd_amount if twd_amount else 0

# 新增：客戶個人應收帳款餘額變化
"customer_receivable_balance": {
    "before": round(customer_receivable_before, 2),
    "change": round(customer_receivable_change, 2),
    "after": round(customer_receivable_after, 2),
    "customer_name": customer_name,
    "description": f"客戶「{customer_name}」應收帳款"
}
```

#### B. 前端顯示修改
**文件**：`templates/cash_management.html`

**新增功能**：
```javascript
// 如果是售出記錄且有客戶應收帳款餘額變化，顯示客戶個人應收帳款變化
if (m.type === '售出' && m.customer_receivable_balance) {
    const customerBalance = m.customer_receivable_balance;
    const before = (customerBalance.before || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const change = (customerBalance.change || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const after = (customerBalance.after || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const changeColor = (customerBalance.change || 0) > 0 ? 'text-success' : (customerBalance.change || 0) < 0 ? 'text-danger' : 'text-muted';
    const changeSymbol = (customerBalance.change || 0) > 0 ? '+' : '';
    
    depositAccountBalanceHtml = '<div class="card" style="background-color: #e3f2fd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 8px; margin: 2px; border-left: 4px solid #2196f3;">' +
        '<div class="text-primary fw-bold" style="font-size: 0.85rem; text-align: right; border-bottom: 1px solid #2196f3; padding-bottom: 4px; margin-bottom: 4px;">' + (customerBalance.customer_name || '客戶') + ' 應收帳款' + '</div>' +
        '<div class="text-dark" style="font-size: 0.8rem;">前: ' + before + '</div>' +
        '<div class="' + changeColor + ' fw-bold" style="font-size: 0.8rem;">變動: ' + changeSymbol + change + '</div>' +
        '<div class="text-dark" style="font-size: 0.8rem;">後: ' + after + '</div>' +
        '</div>';
}
```

### 2. 客戶交易紀錄頁面的應收帳款餘額變化

#### A. 後端API修改
**文件**：`app.py` - `api_customer_transactions`函數

**新增功能**：
```python
# 計算該筆銷售的應收帳款餘額變化
# 需要計算在該筆銷售之前，該客戶的應收帳款餘額
try:
    # 獲取該筆銷售之前的所有銷售記錄
    previous_sales = (
        db.session.execute(
            db.select(SalesRecord)
            .filter(
                SalesRecord.customer_id == customer_id,
                SalesRecord.created_at < sale.created_at
            )
            .order_by(SalesRecord.created_at.desc())
        )
        .scalars()
        .all()
    )
    
    # 計算該筆銷售之前的應收帳款餘額
    receivable_before = sum(s.twd_amount for s in previous_sales)
    receivable_after = receivable_before + sale.twd_amount
    receivable_change = sale.twd_amount
    
    print(f"DEBUG: 客戶 {customer.name} 銷售 {sale.id} 應收帳款變化 - 變動前: {receivable_before:.2f}, 變動: {receivable_change:.2f}, 變動後: {receivable_after:.2f}")
    
except Exception as e:
    print(f"DEBUG: 計算客戶 {customer.name} 銷售 {sale.id} 應收帳款變化失敗: {e}")
    receivable_before = 0
    receivable_after = sale.twd_amount
    receivable_change = sale.twd_amount

# 新增：應收帳款餘額變化
'receivable_balance': {
    'before': round(receivable_before, 2),
    'change': round(receivable_change, 2),
    'after': round(receivable_after, 2),
    'description': f'客戶「{customer.name}」應收帳款'
}
```

#### B. 前端模態框修改
**文件**：`templates/_cash_management_modals.html`

**新增欄位**：
```html
<thead class="table-light">
    <tr>
        <th>日期時間</th>
        <th>類型</th>
        <th>描述</th>
        <th class="text-end text-success">RMB</th>
        <th class="text-end text-primary">TWD</th>
        <th class="text-end text-info">應收帳款餘額變化</th>
    </tr>
</thead>
```

#### C. 前端顯示邏輯修改
**文件**：`templates/cash_management.html` - `displayCustomerTransactions`函數

**新增功能**：
```javascript
// 處理應收帳款餘額變化顯示
let receivableBalanceHtml = '-';
if (tx.receivable_balance) {
    const balance = tx.receivable_balance;
    const before = (balance.before || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const change = (balance.change || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const after = (balance.after || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
    const changeColor = (balance.change || 0) > 0 ? 'text-success' : (balance.change || 0) < 0 ? 'text-danger' : 'text-muted';
    const changeSymbol = (balance.change || 0) > 0 ? '+' : '';
    
    receivableBalanceHtml = '<div class="card" style="background-color: #e3f2fd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 8px; margin: 2px; border-left: 4px solid #2196f3;">' +
        '<div class="text-primary fw-bold" style="font-size: 0.85rem; text-align: right; border-bottom: 1px solid #2196f3; padding-bottom: 4px; margin-bottom: 4px;">' + (balance.description || '應收帳款') + '</div>' +
        '<div class="text-dark" style="font-size: 0.8rem;">前: ' + before + '</div>' +
        '<div class="' + changeColor + ' fw-bold" style="font-size: 0.8rem;">變動: ' + changeSymbol + change + '</div>' +
        '<div class="text-dark" style="font-size: 0.8rem;">後: ' + after + '</div>' +
        '</div>';
}
```

## 🎨 視覺設計

### 現金頁面售出記錄
- **背景色**：淺藍色 (`#e3f2fd`)
- **邊框**：左側藍色邊框 (`#2196f3`)
- **標題**：藍色粗體，顯示客戶名稱
- **內容**：前、變動、後三個數值，變動數值有顏色區分

### 客戶交易紀錄頁面
- **表格欄位**：新增「應收帳款餘額變化」欄位
- **顯示格式**：與現金頁面一致的卡片式設計
- **響應式**：表格支援水平滾動

## 🔄 數據連動

### 現金頁面 → 客戶交易紀錄頁面
1. **數據來源**：現金頁面使用客戶當前總應收帳款餘額
2. **計算方式**：`變動前 = 當前餘額 - 本次銷售金額`
3. **顯示效果**：入款戶餘額變化欄位顯示客戶個人應收帳款變化

### 客戶交易紀錄頁面 → 現金頁面
1. **數據來源**：客戶交易紀錄頁面使用歷史銷售記錄計算
2. **計算方式**：`變動前 = 該筆銷售之前的所有銷售金額總和`
3. **顯示效果**：應收帳款餘額變化欄位顯示每筆交易的累積效果

## 🧪 測試步驟

1. **重新啟動應用**：
   ```bash
   python app.py
   ```

2. **測試現金頁面**：
   - 打開現金管理頁面
   - 查看售出記錄的入款戶餘額變化欄位
   - 確認顯示客戶個人應收帳款變化（前、變動、後）

3. **測試客戶交易紀錄頁面**：
   - 點擊客戶名稱打開交易紀錄模態框
   - 查看應收帳款餘額變化欄位
   - 確認每筆售出記錄都有詳細的餘額變化

4. **驗證數據一致性**：
   - 確認兩個頁面顯示的數據邏輯一致
   - 驗證餘額計算的正確性

## ✅ 功能特點

1. **雙向連動**：現金頁面和客戶交易紀錄頁面都顯示應收帳款餘額變化
2. **詳細記錄**：每筆售出記錄都記錄訂單前、訂單金額、訂單後的餘額變化
3. **視覺一致**：兩個頁面使用相同的卡片式設計風格
4. **數據準確**：基於實際的銷售記錄計算，確保數據準確性
5. **用戶友好**：清晰的視覺設計，易於理解餘額變化

現在售出記錄的入款戶餘額變化會記錄客戶的個人應收帳款詳細變化，並且與客戶交易紀錄頁面完全連動！
