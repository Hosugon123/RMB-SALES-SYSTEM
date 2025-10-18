# 交易紀錄出帳前後餘額對比功能

## 功能概述

本功能增強了交易紀錄的顯示，新增了「出帳前餘額」和「出帳後餘額」兩個欄位，讓用戶能夠清楚看到每筆交易對帳戶餘額的具體影響。

## 主要改進

### 1. 後端API增強 (`app.py`)

在 `/api/cash_management/transactions` API中新增了出帳前後餘額的計算邏輯：

```python
# 計算累積餘額和出帳前後餘額對比
running_twd_balance = 0
running_rmb_balance = 0

# 從最早的記錄開始計算累積餘額
for record in reversed(unified_stream):
    # 記錄出帳前餘額
    record["balance_before_twd"] = running_twd_balance
    record["balance_before_rmb"] = running_rmb_balance
    
    # 計算出帳後餘額
    running_twd_balance += record.get("twd_change", 0)
    running_rmb_balance += record.get("rmb_change", 0)
    record["balance_after_twd"] = running_twd_balance
    record["balance_after_rmb"] = running_rmb_balance
    
    # 保持向後兼容的欄位名稱
    record["running_twd_balance"] = running_twd_balance
    record["running_rmb_balance"] = running_rmb_balance
```

### 2. 前端顯示優化 (`templates/cash_management.html`)

#### 表格結構更新
- 將原本的「累積餘額」欄位拆分為「出帳前餘額」和「出帳後餘額」兩個欄位
- 更新了表格標題和欄位數量

#### JavaScript渲染邏輯
新增了出帳前後餘額的渲染邏輯：

```javascript
// 出帳前餘額顯示
const balanceBeforeTwd = m.balance_before_twd ?? 0;
const balanceBeforeRmb = m.balance_before_rmb ?? 0;
const balanceBeforeHtml = '<div class="small balance-before">' +
    '<div class="text-secondary fw-bold border-bottom border-secondary pb-1 mb-1">NT$ ' + 
    (balanceBeforeTwd || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
    '<div class="text-secondary">¥ ' + 
    (balanceBeforeRmb || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
    '</div>';

// 出帳後餘額顯示
const balanceAfterTwd = m.balance_after_twd ?? m.running_twd_balance ?? m.runningTwdBalance ?? 0;
const balanceAfterRmb = m.balance_after_rmb ?? m.running_rmb_balance ?? m.runningRmbBalance ?? 0;
const balanceAfterHtml = '<div class="small balance-after">' +
    '<div class="text-primary fw-bold border-bottom border-primary pb-1 mb-1">NT$ ' + 
    (balanceAfterTwd || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
    '<div class="text-success">¥ ' + 
    (balanceAfterRmb || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>' +
    '</div>';
```

#### CSS樣式優化
新增了專門的樣式來區分出帳前後餘額：

```css
/* 出帳前餘額列的樣式 */
.balance-before {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 6px;
    padding: 8px;
    border-left: 3px solid #6c757d;
}

/* 出帳後餘額列的樣式 */
.balance-after {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border-radius: 6px;
    padding: 8px;
    border-left: 3px solid #2196f3;
}
```

## 視覺效果

### 出帳前餘額
- 灰色背景漸變
- 灰色邊框
- 顯示交易發生前的帳戶餘額

### 出帳後餘額
- 藍色背景漸變
- 藍色邊框
- 顯示交易發生後的帳戶餘額

## 數據結構

每筆交易記錄現在包含以下額外欄位：

```json
{
    "balance_before_twd": 1383126.079,  // 出帳前TWD餘額
    "balance_before_rmb": 38869.57,     // 出帳前RMB餘額
    "balance_after_twd": 1483126.079,   // 出帳後TWD餘額
    "balance_after_rmb": 38869.57,      // 出帳後RMB餘額
    "running_twd_balance": 1483126.079, // 累積TWD餘額（向後兼容）
    "running_rmb_balance": 38869.57     // 累積RMB餘額（向後兼容）
}
```

## 向後兼容性

- 保留了原有的 `running_twd_balance` 和 `running_rmb_balance` 欄位
- 如果新的欄位不存在，會自動回退到舊的欄位名稱
- 不影響現有的其他功能

## 測試

創建了測試頁面 `test_transaction_balance_comparison.html` 來驗證功能的正確性，包含：
- 模擬交易數據
- 完整的表格顯示
- 樣式效果展示

## 使用說明

1. 進入現金管理頁面
2. 查看「近期交易記錄」表格
3. 現在可以看到每筆交易的：
   - 出帳前餘額（灰色背景）
   - 出帳後餘額（藍色背景）
   - 清楚看出每筆交易對帳戶餘額的影響

## 技術細節

- 後端計算順序：從最早的交易開始，按時間順序累積計算
- 前端顯示順序：最新的交易顯示在最上方
- 金額格式化：使用千分位分隔符，保留兩位小數
- 響應式設計：表格支援橫向滾動，適應不同螢幕尺寸
