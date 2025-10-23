# 現金頁面售出記錄應收帳款餘額變化卡片移植

## 🎯 移植目標

將圖2（客戶交易紀錄頁面）的應收帳款餘額變化卡片運算邏輯以及顯示樣式直接移植到現金頁面交易紀錄的售出記錄入款戶餘額變化欄位。

## 🔧 已完成的移植

### 1. 後端計算邏輯移植

**文件**：`app.py` - `get_cash_management_transactions`函數

**移植前（錯誤邏輯）**：
```python
# 使用客戶當前總應收帳款餘額計算（不準確）
customer_receivable_after = customer.total_receivables_twd if customer else 0
customer_receivable_before = customer_receivable_after - twd_amount
customer_receivable_change = twd_amount
```

**移植後（與客戶交易紀錄頁面完全一致）**：
```python
# 計算客戶個人應收帳款餘額變化（使用與客戶交易紀錄頁面相同的邏輯）
if customer:
    # 獲取該筆銷售之前的所有銷售記錄（與客戶交易紀錄頁面相同的邏輯）
    previous_sales = (
        db.session.execute(
            db.select(SalesRecord)
            .filter(
                SalesRecord.customer_id == customer.id,
                SalesRecord.created_at < s.created_at
            )
            .order_by(SalesRecord.created_at.desc())
        )
        .scalars()
        .all()
    )
    
    # 計算該筆銷售之前的應收帳款餘額（與客戶交易紀錄頁面相同的邏輯）
    customer_receivable_before = sum(sale.twd_amount for sale in previous_sales)
    customer_receivable_after = customer_receivable_before + twd_amount
    customer_receivable_change = twd_amount
```

### 2. 前端顯示樣式移植

**文件**：`templates/cash_management.html`

**移植的樣式（與客戶交易紀錄頁面完全一致）**：
```javascript
// 使用與客戶交易紀錄頁面完全一致的樣式
depositAccountBalanceHtml = '<div class="card" style="background-color: #e3f2fd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 8px; margin: 2px; border-left: 4px solid #2196f3;">' +
    '<div class="text-primary fw-bold" style="font-size: 0.85rem; text-align: right; border-bottom: 1px solid #2196f3; padding-bottom: 4px; margin-bottom: 4px;">' + (customerBalance.description || '應收帳款') + '</div>' +
    '<div class="text-dark" style="font-size: 0.8rem;">前: ' + before + '</div>' +
    '<div class="' + changeColor + ' fw-bold" style="font-size: 0.8rem;">變動: ' + changeSymbol + change + '</div>' +
    '<div class="text-dark" style="font-size: 0.8rem;">後: ' + after + '</div>' +
    '</div>';
```

## 🎨 移植的視覺效果

### 卡片樣式（與客戶交易紀錄頁面完全一致）
- **背景色**：淺藍色 (`#e3f2fd`)
- **邊框**：左側藍色邊框 (`#2196f3`)
- **圓角**：8px
- **陰影**：`0 2px 4px rgba(0,0,0,0.1)`
- **內邊距**：8px
- **外邊距**：2px

### 內容結構
1. **標題**：`客戶「客戶名稱」應收帳款`（藍色粗體，右對齊，底部邊框）
2. **前**：變動前餘額（深色文字）
3. **變動**：變動金額（綠色/紅色，帶+/-符號）
4. **後**：變動後餘額（深色文字）

## 🔄 計算邏輯對比

### 客戶交易紀錄頁面（圖2）
```python
# 獲取該筆銷售之前的所有銷售記錄
previous_sales = db.session.execute(
    db.select(SalesRecord)
    .filter(
        SalesRecord.customer_id == customer_id,
        SalesRecord.created_at < sale.created_at
    )
).scalars().all()

# 計算該筆銷售之前的應收帳款餘額
receivable_before = sum(s.twd_amount for s in previous_sales)
receivable_after = receivable_before + sale.twd_amount
receivable_change = sale.twd_amount
```

### 現金頁面（移植後）
```python
# 獲取該筆銷售之前的所有銷售記錄（與客戶交易紀錄頁面相同的邏輯）
previous_sales = db.session.execute(
    db.select(SalesRecord)
    .filter(
        SalesRecord.customer_id == customer.id,
        SalesRecord.created_at < s.created_at
    )
).scalars().all()

# 計算該筆銷售之前的應收帳款餘額（與客戶交易紀錄頁面相同的邏輯）
customer_receivable_before = sum(sale.twd_amount for sale in previous_sales)
customer_receivable_after = customer_receivable_before + twd_amount
customer_receivable_change = twd_amount
```

## ✅ 移植完成的功能

1. **計算邏輯完全一致**：使用相同的歷史銷售記錄計算方式
2. **顯示樣式完全一致**：使用相同的卡片設計和顏色方案
3. **數據結構完全一致**：使用相同的`receivable_balance`結構
4. **調試信息一致**：使用相同的調試日誌格式

## 🧪 測試步驟

1. **重新啟動應用**：
   ```bash
   python app.py
   ```

2. **測試現金頁面**：
   - 打開現金管理頁面
   - 查看售出記錄的入款戶餘額變化欄位
   - 確認顯示與客戶交易紀錄頁面完全一致的應收帳款餘額變化卡片

3. **測試客戶交易紀錄頁面**：
   - 點擊客戶名稱打開交易紀錄模態框
   - 確認應收帳款餘額變化欄位正常顯示

4. **對比兩個頁面**：
   - 確認兩個頁面顯示的應收帳款餘額變化卡片完全一致
   - 驗證計算邏輯和顯示樣式的一致性

## 🎯 預期效果

現在現金頁面的售出記錄的入款戶餘額變化欄位會顯示與客戶交易紀錄頁面完全一致的應收帳款餘額變化卡片：

```
┌─────────────────────────┐
│ 客戶「胡」應收帳款        │
│ 前: 1,776.00            │
│ 變動: +25.00            │
│ 後: 1,801.00            │
└─────────────────────────┘
```

**特點**：
- 與客戶交易紀錄頁面完全一致的計算邏輯
- 與客戶交易紀錄頁面完全一致的顯示樣式
- 準確的歷史銷售記錄累積計算
- 統一的視覺設計語言

現在現金頁面的售出記錄入款戶餘額變化欄位已經完全移植了客戶交易紀錄頁面的應收帳款餘額變化卡片！
