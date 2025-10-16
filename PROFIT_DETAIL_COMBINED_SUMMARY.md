# 🎯 利潤變動詳情合併顯示實現總結

## 功能需求

**用戶需求：** 將三個利潤欄位（變動前利潤、變動後利潤、變動之利潤數字）合併為一個欄位，模仿累積餘額的顯示方式。

**實現目標：** 在一個欄位內顯示完整的利潤變動信息，節省表格空間並保持視覺一致性。

## 實現內容

### ✅ 1. 表格結構調整

#### A. 表頭修改
**文件：** `templates/cash_management.html`

**修改前：**
```html
<th class="text-end">累積餘額</th>
<th class="text-end">變動前利潤</th>
<th class="text-end">變動後利潤</th>
<th class="text-end pe-3">變動之利潤數字</th>
```

**修改後：**
```html
<th class="text-end">累積餘額</th>
<th class="text-end pe-3">利潤變動詳情</th>
```

#### B. 列數調整
- 從 13 列減少到 11 列
- 更新所有 `colspan` 引用

### ✅ 2. JavaScript 渲染邏輯

#### A. 利潤變動詳情 HTML 生成
```javascript
// 利潤變動詳情（模仿累積餘額的顯示方式）
let profitDetailHtml = '-';
if (profitBefore !== null && profitAfter !== null && profitChange !== null) {
    // 有利潤變動記錄，顯示詳細信息
    const changeColorClass = profitChange > 0 ? 'text-success' : 'text-danger';
    const changeSymbol = profitChange > 0 ? '+' : '';
    
    profitDetailHtml = '<div class="small running-balance">' +
        '<div class="text-info fw-bold border-bottom border-info pb-1 mb-1">前: ' + profitBeforeDisplay + '</div>' +
        '<div class="text-info border-bottom border-info pb-1 mb-1">後: ' + profitAfterDisplay + '</div>' +
        '<div class="' + changeColorClass + ' fw-bold">變: ' + changeSymbol + profitChangeDisplay + '</div>' +
        '</div>';
} else if (profit !== 0) {
    // 有傳統利潤記錄，顯示簡單信息
    profitDetailHtml = '<div class="small">' +
        '<div class="' + profitColorClass + '">' + profitDisplay + '</div>' +
        '</div>';
}
```

#### B. 表格行渲染
```javascript
const row = '<tr class="transaction-row">' +
    // ... 其他欄位 ...
    '<td class="text-end">' + runningBalanceHtml + '</td>' +
    '<td class="text-end pe-3">' + profitDetailHtml + '</td>' +
    '</tr>';
```

### ✅ 3. 顯示邏輯

#### A. 三種顯示模式

1. **利潤提款記錄**：
   ```
   前: 20,351.00
   後: 19,951.00
   變: -400.00
   ```

2. **資產提款記錄**：
   ```
   -
   ```

3. **其他記錄**：
   ```
   +150.00
   ```

#### B. 視覺設計
- **前/後利潤**：藍色文字（`text-info`）
- **變動金額**：綠色（增加）或紅色（減少）
- **框體樣式**：使用 `running-balance` 類，與累積餘額保持一致

## 功能特點

### 📊 **統一顯示方式**
- 模仿累積餘額的框體設計
- 使用相同的樣式和布局
- 保持視覺一致性

### 🎨 **清晰的數據層次**
- **前:** 變動前利潤
- **後:** 變動後利潤  
- **變:** 變動金額

### 🔧 **智能顯示邏輯**
- 根據記錄類型顯示不同內容
- 自動處理缺失數據
- 向後兼容舊記錄

## 顯示效果

### 📋 **利潤提款記錄**
```
┌─────────────────┐
│ 前: 20,351.00   │
├─────────────────┤
│ 後: 19,951.00   │
├─────────────────┤
│ 變: -400.00     │
└─────────────────┘
```

### 📋 **資產提款記錄**
```
-
```

### 📋 **其他記錄**
```
+150.00
```

## 技術實現

### 🏗️ **HTML 結構**
```html
<div class="small running-balance">
    <div class="text-info fw-bold border-bottom border-info pb-1 mb-1">前: 20,351.00</div>
    <div class="text-info border-bottom border-info pb-1 mb-1">後: 19,951.00</div>
    <div class="text-danger fw-bold">變: -400.00</div>
</div>
```

### 🎨 **CSS 樣式**
- 使用 `running-balance` 類提供背景和圓角
- 使用 `border-bottom` 分隔線
- 使用 `text-info`、`text-success`、`text-danger` 顏色類

### 📱 **響應式設計**
- 保持與累積餘額相同的響應式特性
- 在小螢幕上自動調整

## 優點

### ✅ **空間效率**
- 從 13 列減少到 11 列
- 節省表格橫向空間
- 提高數據密度

### ✅ **視覺一致性**
- 與累積餘額使用相同的設計語言
- 統一的視覺風格
- 更好的用戶體驗

### ✅ **信息完整性**
- 保留所有利潤變動信息
- 清晰的數據層次
- 易於理解的顯示方式

## 測試驗證

### 🧪 **測試頁面**
- **`test_profit_detail_combined.html`** - 合併顯示測試頁面

### 📝 **測試內容**
- 利潤提款記錄的詳細顯示
- 資產提款記錄的簡單顯示
- 其他記錄的傳統顯示
- 視覺樣式和顏色

### ✅ **驗證要點**
- 表格列數正確（11 列）
- 利潤變動詳情框顯示正確
- 顏色和樣式符合設計
- 不同記錄類型顯示適當

## 相關文件

### 📁 **修改的文件**
- `templates/cash_management.html` - 前端顯示邏輯

### 📁 **新增的測試文件**
- `test_profit_detail_combined.html` - 合併顯示測試

### 📁 **相關功能**
- 利潤詳細記錄功能
- 累積餘額顯示
- 現金管理頁面

## 預期效果

實現後，用戶將體驗到：

1. ✅ **更緊湊的表格** - 減少列數，提高空間利用率
2. ✅ **一致的視覺風格** - 與累積餘額保持相同的設計
3. ✅ **完整的利潤信息** - 在一個欄位內顯示所有相關數據
4. ✅ **清晰的数据層次** - 前、後、變動一目了然
5. ✅ **更好的可讀性** - 結構化的信息展示

---

**結論：** 成功將三個利潤欄位合併為一個「利潤變動詳情」欄位，模仿累積餘額的顯示方式，在保持信息完整性的同時提高了表格的空間效率和視覺一致性。


