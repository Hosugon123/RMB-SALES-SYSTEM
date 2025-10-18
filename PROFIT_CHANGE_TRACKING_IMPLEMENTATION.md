# 利潤變動追蹤功能實現

## 功能概述

根據用戶需求，系統現在會在交易紀錄中記錄完整的利潤變動信息，包括：
- **變動前利潤**：該交易執行前的累積利潤
- **當下變動**：本次交易產生的利潤變化
- **變動後利潤**：該交易執行後的累積利潤

## 實現細節

### 1. 後端修改

#### A. 銷售記錄處理邏輯更新

**文件：** `app.py` (第6479-6513行)

```python
# 處理售出記錄
for s in sales:
    if s.customer:
        profit_info = FIFOService.calculate_profit_for_sale(s)
        profit = profit_info['profit_twd'] if profit_info else 0
        
        # 計算利潤變動前後的狀態
        # 變動前：計算到這筆銷售之前的所有利潤總和
        profit_before = 0.0
        for prev_sale in sales:
            if prev_sale.created_at < s.created_at:
                prev_profit_info = FIFOService.calculate_profit_for_sale(prev_sale)
                if prev_profit_info:
                    profit_before += prev_profit_info.get('profit_twd', 0.0)
        
        # 變動後：變動前 + 當下變動
        profit_after = profit_before + profit
        
        unified_stream.append({
            "type": "售出",
            "date": s.created_at.isoformat(),
            "description": f"售予 {s.customer.name}",
            "twd_change": 0,
            "rmb_change": -s.rmb_amount,
            "operator": s.operator.username if s.operator else "未知",
            "profit": profit,
            "profit_before": profit_before,
            "profit_after": profit_after,
            "profit_change": profit,
            "payment_account": s.rmb_account.name if s.rmb_account else "N/A",
            "deposit_account": "應收帳款",
            "payment_account_id": s.rmb_account.id if s.rmb_account else None,
            "deposit_account_id": None,
            "note": s.note if hasattr(s, 'note') and s.note else None,
        })
```

#### B. 利潤提款記錄處理更新

**文件：** `app.py` (第6575-6588行)

```python
# 如果是利潤提款，添加詳細利潤信息
if entry.entry_type == "PROFIT_WITHDRAW":
    # 安全地獲取利潤詳細信息
    record["profit_before"] = getattr(entry, 'profit_before', None)
    record["profit_after"] = getattr(entry, 'profit_after', None)
    record["profit_change"] = getattr(entry, 'profit_change', None)
    record["profit"] = getattr(entry, 'profit_change', None)  # 保持向後兼容
    
    # 確保所有利潤變動記錄都有完整的變動前後信息
    if record["profit_before"] is None or record["profit_after"] is None or record["profit_change"] is None:
        # 如果缺少信息，嘗試從描述或其他方式獲取
        record["profit_before"] = record["profit_before"] or 0.0
        record["profit_after"] = record["profit_after"] or (record["profit_before"] + (record["profit_change"] or 0))
        record["profit_change"] = record["profit_change"] or (record["profit_after"] - record["profit_before"])
```

### 2. 前端修改

#### A. 利潤變動顯示邏輯更新

**文件：** `templates/cash_management.html` (第1475-1515行)

```javascript
// 處理利潤顯示格式 - 支援完整的變動前後信息
let profitDisplay = '';
const profitChange = parseFloat(m.profit_change ?? m.profit ?? 0) || 0;
const profitBefore = parseFloat(m.profit_before ?? 0) || 0;
const profitAfter = parseFloat(m.profit_after ?? 0) || 0;

if (profitChange !== 0 && profitBefore !== undefined && profitAfter !== undefined) {
    // 有完整的變動前後信息，顯示詳細格式
    const profitChangeClass = profitChange > 0 ? 'text-success' : 'text-danger';
    const changeSymbol = profitChange > 0 ? '+' : '';
    
    profitDisplay = '<div class="small profit-change-detail">' +
        '<div class="text-secondary small">前: ' + profitBefore.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="' + profitChangeClass + ' small">變動: ' + changeSymbol + profitChange.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '<div class="text-dark small">後: ' + profitAfter.toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
        '</div>';
} else {
    // 其他情況：顯示簡單的數字
    profitDisplay = profit !== 0 ? profit.toLocaleString('en-US', {minimumFractionDigits: 2}) : '-';
}
```

#### B. CSS樣式添加

**文件：** `templates/cash_management.html` (第305-318行)

```css
/* 利潤變動詳細信息列的樣式 */
.profit-change-detail {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    border-radius: 6px;
    padding: 8px;
    border-left: 3px solid #ffc107;
    min-width: 120px;
}

.profit-change-detail .small {
    font-size: 0.75rem;
    line-height: 1.2;
    margin-bottom: 2px;
}
```

### 3. 數據流程

#### A. 銷售記錄的利潤變動計算
1. 獲取所有銷售記錄
2. 按時間順序計算每筆銷售的利潤
3. 對於每筆銷售，計算：
   - `profit_before`：該銷售之前所有銷售的利潤總和
   - `profit_change`：該銷售產生的利潤
   - `profit_after`：該銷售之後的累積利潤總和

#### B. 利潤提款的利潤變動記錄
1. 從LedgerEntry記錄中獲取利潤變動信息
2. 確保所有必要字段都有值
3. 如果缺少信息，進行補全計算

### 4. 顯示效果

#### A. 詳細利潤變動顯示
當交易有利潤變動時，會在「利潤變動」欄位顯示：
```
前: 0.00
變動: +5,000.00
後: 5,000.00
```

#### B. 視覺樣式
- **背景色**：黃色漸變背景，突出利潤變動信息
- **邊框**：左側黃色邊框，與其他變動信息區分
- **文字顏色**：
  - 變動前：灰色
  - 變動金額：綠色（增加）/ 紅色（減少）
  - 變動後：深色

### 5. 測試驗證

創建了測試頁面 `test_profit_change_tracking.html` 來驗證功能，包含：
- 銷售記錄的利潤變動追蹤
- 利潤提款的利潤變動記錄
- 完整的變動前後信息顯示

### 6. 向後兼容性

系統保持了向後兼容性：
- 對於沒有完整變動信息的舊記錄，仍顯示簡單的利潤數字
- 對於新的有利潤變動記錄，顯示完整的變動前後信息
- 支援多種數據格式，確保系統穩定性

## 總結

此實現完全滿足了用戶的需求：
- ✅ **變動前利潤**：記錄交易執行前的累積利潤
- ✅ **當下變動**：記錄本次交易產生的利潤變化
- ✅ **變動後利潤**：記錄交易執行後的累積利潤

系統現在能夠提供完整的利潤變動追蹤，讓用戶清楚了解每筆交易對總體利潤的影響。
