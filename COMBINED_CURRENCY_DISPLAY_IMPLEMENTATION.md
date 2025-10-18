# 合併幣別變動顯示功能實現

## 功能概述

根據用戶需求，系統現在將TWD變動和RMB變動合併到同一欄顯示，用清楚的字樣和字體顏色來區分不同的幣別變動。

## 實現細節

### 1. 表格標題修改

**文件：** `templates/cash_management.html` (第246行)

```html
<th class="text-end">TWD/RMB 變動</th>
```

將原本的兩個獨立欄位：
- `TWD 變動`
- `RMB 變動`

合併為一個欄位：
- `TWD/RMB 變動`

### 2. 前端顯示邏輯修改

#### A. 第一個renderMovements函數

**文件：** `templates/cash_management.html` (第1583-1619行)

```javascript
// 格式化金額顯示 - 合併TWD和RMB變動到一欄
let currencyChangeDisplay = '';

if (twdChange !== 0 && rmbChange !== 0) {
    // 兩種幣別都有變動
    const twdClass = twdChange > 0 ? 'text-success' : 'text-danger';
    const rmbClass = rmbChange > 0 ? 'text-success' : 'text-danger';
    const twdSymbol = twdChange > 0 ? '+' : '';
    const rmbSymbol = rmbChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-combined">' +
        '<div class="' + twdClass + ' fw-bold">TWD: ' + twdSymbol + twdChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="' + rmbClass + ' fw-bold">RMB: ' + rmbSymbol + rmbChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else if (twdChange !== 0) {
    // 只有TWD變動
    const twdClass = twdChange > 0 ? 'text-success' : 'text-danger';
    const twdSymbol = twdChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-single">' +
        '<div class="' + twdClass + ' fw-bold">TWD: ' + twdSymbol + twdChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else if (rmbChange !== 0) {
    // 只有RMB變動
    const rmbClass = rmbChange > 0 ? 'text-success' : 'text-danger';
    const rmbSymbol = rmbChange > 0 ? '+' : '';
    
    currencyChangeDisplay = '<div class="small currency-change-single">' +
        '<div class="' + rmbClass + ' fw-bold">RMB: ' + rmbSymbol + rmbChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else {
    // 沒有變動
    currencyChangeDisplay = '-';
}
```

#### B. 第二個renderMovements函數（全局函數）

**文件：** `templates/cash_management.html` (第2376-2409行)

使用相同的邏輯處理幣別變動顯示。

### 3. 表格行渲染修改

#### A. 第一個renderMovements函數

**文件：** `templates/cash_management.html` (第1672行)

```javascript
'<td class="text-end">' + currencyChangeDisplay + '</td>' +
```

#### B. 第二個renderMovements函數

**文件：** `templates/cash_management.html` (第2499行)

```javascript
'<td class="text-end">' + currencyChangeDisplay + '</td>' +
```

### 4. CSS樣式添加

**文件：** `templates/cash_management.html` (第319-341行)

```css
/* 幣別變動合併顯示的樣式 */
.currency-change-combined {
    background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
    border-radius: 6px;
    padding: 6px;
    border-left: 3px solid #17a2b8;
    min-width: 100px;
}

.currency-change-single {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 6px;
    padding: 6px;
    border-left: 3px solid #6c757d;
    min-width: 100px;
}

.currency-change-combined .small,
.currency-change-single .small {
    font-size: 0.75rem;
    line-height: 1.2;
    margin-bottom: 2px;
}
```

### 5. 顯示效果

#### A. 只有TWD變動
```
TWD: +100,000.00
```

#### B. 只有RMB變動
```
RMB: -1,000.00
```

#### C. 兩種幣別都有變動
```
TWD: -50,000.00
RMB: +10,000.00
```

#### D. 沒有變動
```
-
```

### 6. 視覺樣式特點

#### A. 顏色區分
- **綠色** (`text-success`)：正數變動（增加）
- **紅色** (`text-danger`)：負數變動（減少）
- **灰色** (`text-muted`)：無變動

#### B. 背景樣式
- **合併顯示** (`.currency-change-combined`)：藍色漸變背景，用於兩種幣別都有變動的情況
- **單一顯示** (`.currency-change-single`)：灰色漸變背景，用於只有一種幣別變動的情況

#### C. 字體樣式
- **粗體** (`fw-bold`)：幣別標籤和金額數字
- **小字體** (`small`)：整體縮小以節省空間
- **清楚標籤**：明確標示「TWD:」和「RMB:」

### 7. 測試驗證

創建了測試頁面 `test_combined_currency_display.html` 來驗證功能，包含：
- 只有TWD變動的交易記錄
- 只有RMB變動的交易記錄
- 兩種幣別都有變動的交易記錄
- 沒有變動的交易記錄

### 8. 優化效果

#### A. 空間節省
- 原本需要兩欄顯示的TWD和RMB變動，現在合併為一欄
- 表格更緊湊，可以顯示更多信息

#### B. 視覺清晰
- 用顏色清楚區分正負變動
- 用字體樣式突出幣別標籤
- 用背景色區分顯示類型

#### C. 信息完整
- 保持了所有原有的變動信息
- 清楚標示幣別類型
- 維持了數字的可讀性

## 總結

此實現完全滿足了用戶的需求：
- ✅ **合併顯示**：TWD變動和RMB變動合併到同一欄
- ✅ **清楚字樣**：明確標示「TWD:」和「RMB:」標籤
- ✅ **字體顏色區分**：用綠色/紅色區分正負變動
- ✅ **視覺優化**：用背景色和樣式區分不同顯示情況

系統現在能夠在更緊湊的空間內顯示完整的幣別變動信息，同時保持良好的可讀性和視覺效果。
