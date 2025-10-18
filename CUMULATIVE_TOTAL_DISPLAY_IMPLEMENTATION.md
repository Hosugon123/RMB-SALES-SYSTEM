# 累積總金額顯示功能實現

## 功能概述

根據用戶需求，系統現在在「TWD/RMB 變動」欄位中同時記錄和顯示兩種貨幣的當前總金額變化，不僅顯示當次的變動金額，還顯示累積的總金額。

## 實現細節

### 1. 後端邏輯修改

#### A. 記錄收集和處理

**文件：** `app.py` (第6463-6672行)

```python
# 先收集所有記錄，然後計算累積總金額
all_records = []

# 處理買入記錄
for p in purchases:
    if p.payment_account and p.deposit_account:
        # ... 處理邏輯 ...
        all_records.append({
            "type": "買入",
            "date": p.purchase_date.isoformat(),
            "description": f"向 {channel_name} 買入",
            "twd_change": -p.twd_cost,
            "rmb_change": p.rmb_amount,
            # ... 其他字段 ...
        })

# 處理售出記錄
for s in sales:
    # ... 處理邏輯 ...
    all_records.append({
        "type": "售出",
        "date": s.created_at.isoformat(),
        "description": f"售予 {s.customer.name}",
        "twd_change": 0,
        "rmb_change": -s.rmb_amount,
        # ... 其他字段 ...
    })

# 處理其他記帳記錄和現金日誌記錄
# ... 類似邏輯 ...
```

#### B. 累積總金額計算

**文件：** `app.py` (第6650- sms72行)

```python
# 計算每個記錄的累積總金額變化
# 按時間順序排序（最早的在前）
chronological_records = sorted(all_records, key=lambda x: x["date"])

# 計算累積總金額
running_twd_total = 0.0
running_rmb_total = 0.0

for record in chronological_records:
    # 記錄當前的累積總金額（變動前）
    record["twd_total_before"] = running_twd_total
    record["rmb_total_before"] = running_rmb_total
    
    # 更新累積總金額
    running_twd_total += record.get("twd_change", 0)
    running_rmb_total += record.get("rmb_change", 0)
    
    # 記錄變動後的累積總金額
    record["twd_total_after"] = running_twd_total
    record["rmb_total_after"] = running_rmb_total

# 按日期排序（新的在前）
unified_stream = sorted(all_records, key=lambda x: x["date"], reverse=True)
```

### 2. 前端顯示邏輯修改

#### A. 第一個renderMovements函數

**文件：** `templates/cash_management.html` (第1611-1654行)

```javascript
// 格式化金額顯示 - 合併TWD和RMB變動到一欄，包含累積總金額
let currencyChangeDisplay = '';

// 獲取累積總金額信息
const twdTotalBefore = parseFloat(m.twd_total_before ?? 0) || 0;
const twdTotalAfter = parseFloat(m.twd_total_after ?? 0) || 0;
const rmbTotalBefore = parseFloat(m.rmb_total_before ?? 0) || 0;
const rmbTotalAfter = parseFloat(m.rmb_total_after ?? 0) || 0;

if (twdChange !== 0 && rmbChange !== 0) {
    // 兩種幣別都有變動
    const twdClass = twdChange > 0 ? 'text-success' : 'text-danger';
    const rmbClass = rmbChange > 0 ? 'text-success' : 'text-danger';
    const twdSymbol = twdChange > 0 ? '+' : '';
    const rmbSymbol = rmbChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-combined">' +
        '<div class="' + twdClass + ' fw-bold">TWD: ' + twdSymbol + twdChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-secondary small">總額: ' + twdTotalAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="' + rmbClass + ' fw-bold">RMB: ' + rmbSymbol + rmbChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-secondary small">總額: ' + rmbTotalAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else if (twdChange !== 0) {
    // 只有TWD變動
    const twdClass = twdChange > 0 ? 'text-success' : 'text-danger';
    const twdSymbol = twdChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-single">' +
        '<div class="' + twdClass + ' fw-bold">TWD: ' + twdSymbol + twdChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-secondary small">總額: ' + twdTotalAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else if (rmbChange !== 0) {
    // 只有RMB變動
    const rmbClass = rmbChange > 0 ? 'text-success' : 'text-danger';
    const rmbSymbol = rmbChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-single">' +
        '<div class="' + rmbClass + ' fw-bold">RMB: ' + rmbSymbol + rmbChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-secondary small">總額: ' + rmbTotalAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else {
    // 沒有變動
    currencyChangeDisplay = '-';
}
```

#### B. 第二個renderMovements函數（全局函數）

**文件：** `templates/cash_management.html` (第2413-2456行)

使用相同的邏輯處理累積總金額顯示。

### 3. 顯示效果

#### A. 兩種幣別都有變動的情況

```
TWD: -50,000.00
總額: -50,000.00
RMB: +10,000.00
總額: 10,000.00
```

#### B. 只有TWD變動的情況

```
TWD: +100,000.00
總額: 50,000.00
```

#### C. 只有RMB變動的情況

```
RMB: -2,000.00
總額: 8,000.00
```

#### D. 沒有變動的情況

```
-
```

### 4. 數據流程

#### A. 累積總金額計算流程
1. **收集所有記錄**：將所有交易記錄收集到 `all_records` 列表中
2. **時間排序**：按時間順序排序（最早的在前）
3. **累積計算**：從最早的記錄開始，累積計算每筆交易的總金額
4. **記錄總額**：為每筆交易記錄添加 `twd_total_before`、`twd_total_after`、`rmb_total_before`、`rmb_total_after` 字段
5. **最終排序**：按時間倒序排序（最新的在前）用於顯示

#### B. 前端顯示流程
1. **獲取數據**：從後端API獲取包含累積總金額的交易記錄
2. **解析總額**：解析 `twd_total_before`、`twd_total_after`、`rmb_total_before`、`rmb_total_after` 字段
3. **格式化顯示**：根據變動情況格式化顯示內容
4. **渲染界面**：將格式化後的內容渲染到交易記錄表格中

### 5. 視覺樣式特點

#### A. 顏色區分
- **當次變動**：綠色（增加）/ 紅色（減少），粗體顯示
- **累積總額**：灰色，普通字體顯示
- **背景樣式**：藍色漸變（合併顯示）/ 灰色漸變（單一顯示）

#### B. 信息層次
- **第一行**：當次變動金額（突出顯示）
- **第二行**：累積總額（輔助信息）
- **多幣別**：TWD和RMB分別顯示，各自有變動和總額

### 6. 測試驗證

創建了測試頁面 `test_cumulative_total_display.html` 來驗證功能，包含：
- 買入交易（兩種幣別都有變動）
- 售出交易（只有RMB變動）
- 銷帳交易（只有TWD變動）
- 轉帳交易（兩種幣別都有變動）

### 7. 功能優勢

#### A. 信息完整性
- 同時顯示當次變動和累積總額
- 兩種幣別的變動和總額分別顯示
- 清楚的視覺層次區分

#### B. 實用性提升
- 用戶可以快速了解每筆交易的影響
- 累積總額幫助用戶掌握整體資金狀況
- 減少需要額外計算的步驟

#### C. 視覺效果
- 清楚的顏色區分（變動 vs 總額）
- 合適的字體樣式（粗體 vs 普通）
- 一致的背景樣式

## 總結

此實現完全滿足了用戶的需求：
- ✅ **當次變動顯示**：清楚顯示每次交易的TWD和RMB變動
- ✅ **累積總額顯示**：顯示到該筆交易為止的累積總金額
- ✅ **兩種幣別同時記錄**：TWD和RMB的變動和總額分別顯示
- ✅ **視覺層次清楚**：用顏色和字體區分不同類型的信息

系統現在能夠提供完整的貨幣變動追蹤，讓用戶清楚了解每筆交易對總體資金狀況的具體影響，同時掌握累積的總金額變化。
