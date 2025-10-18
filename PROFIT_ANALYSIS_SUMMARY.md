# 利潤數字分析報告

## 利潤計算機制分析

經過詳細檢查系統代碼，我可以確認**利潤數字是獨立計算且可以動用的**，具體分析如下：

### 1. 利潤計算方式

#### A. 動態計算（非純粹顯示）
利潤是通過 `FIFOService.calculate_profit_for_sale()` 方法**動態計算**的：

```python
def calculate_profit_for_sale(sales_record):
    """計算某筆銷售的利潤（使用FIFO方法）"""
    # 獲取該銷售記錄的所有FIFO分配
    allocations = db.session.execute(
        db.select(FIFOSalesAllocation)
        .filter(FIFOSalesAllocation.sales_record_id == sales_record.id)
    ).scalars().all()
    
    # 使用FIFO分配計算利潤
    total_profit_twd = 0
    sales_exchange_rate = sales_record.twd_amount / sales_record.rmb_amount
    
    for allocation in allocations:
        # 計算每筆分配的利潤
        profit = (sales_exchange_rate - allocation.unit_cost_twd) * allocation.allocated_rmb
        total_profit_twd += profit
    
    return {
        'profit_twd': total_profit_twd,
        'profit_margin': (total_profit_twd / sales_record.twd_amount * 100) if sales_record.twd_amount > 0 else 0,
        'total_cost_twd': total_cost_twd
    }
```

#### B. 計算邏輯
- **FIFO原則**：按照先進先出原則分配庫存成本
- **即時計算**：每次查詢時重新計算，確保數據準確性
- **成本追蹤**：追蹤每筆銷售對應的具體買入成本

### 2. 利潤可動用性

#### A. 利潤提款功能
系統提供完整的利潤提款機制：

```python
# 提款類型判斷
withdraw_type = request.form.get("withdraw_type", "asset")  # "profit" 或 "asset"

if withdraw_type == "profit":
    # 利潤提款處理
    description = "利潤提款"
    entry_type = "PROFIT_WITHDRAW"
    
    # 計算當前總利潤
    current_total_profit = 0.0
    all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
    
    for sale in all_sales:
        profit_info = FIFOService.calculate_profit_for_sale(sale)
        if profit_info:
            current_total_profit += profit_info.get('profit_twd', 0.0)
    
    # 扣除之前的利潤提款
    previous_profit_withdrawals = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
    ).scalars().all()
    
    previous_withdrawals = sum(entry.amount for entry in previous_profit_withdrawals)
    current_total_profit -= previous_withdrawals
```

#### B. 提款記錄追蹤
- **LedgerEntry記錄**：每次利潤提款都會創建 `PROFIT_WITHDRAW` 類型的流水記錄
- **餘額追蹤**：系統會記錄提款前後的利潤餘額變化
- **審計功能**：完整的操作記錄和審計日誌

### 3. 利潤顯示邏輯

#### A. 儀表板計算
```python
# 計算總銷售利潤
total_profit_twd = 0.0
for sale in all_sales:
    profit_info = FIFOService.calculate_profit_for_sale(sale)
    if profit_info:
        total_profit_twd += profit_info.get('profit_twd', 0.0)

# 扣除利潤提款記錄
profit_withdrawals = db.session.execute(
    db.select(LedgerEntry)
    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
).scalars().all()

total_profit_withdrawals = sum(entry.amount for entry in profit_withdrawals)
total_profit_twd -= total_profit_withdrawals  # 顯示可動用利潤
```

#### B. 交易記錄顯示
```python
# 每筆銷售記錄都會顯示對應的利潤
profit_info = FIFOService.calculate_profit_for_sale(sale)
profit_twd = profit_info.get('profit_twd', 0.0) if profit_info else 0.0

unified_stream.append({
    "type": "售出",
    "description": f"向 {s.customer.name} 售出",
    "note": f"利潤: {profit_twd:.2f} TWD" if profit_twd > 0 else None,
})
```

### 4. 系統特性總結

#### ✅ **利潤是獨立計算的**
- 基於FIFO庫存管理原則
- 即時計算，確保數據準確性
- 追蹤每筆銷售的具體成本分配

#### ✅ **利潤是可以動用的**
- 提供完整的利潤提款功能
- 區分利潤提款和資產提款
- 完整的提款記錄和審計追蹤

#### ✅ **利潤顯示是動態的**
- 儀表板顯示扣除提款後的可動用利潤
- 交易記錄顯示每筆銷售的具體利潤
- 支援利潤提款記錄的詳細追蹤

### 5. 實際操作流程

1. **銷售產生利潤**：每筆銷售根據FIFO原則計算利潤
2. **利潤累積**：系統累積所有銷售的利潤總額
3. **利潤提款**：用戶可以選擇「利潤提款」類型進行提款
4. **餘額更新**：提款後更新可動用利潤餘額
5. **記錄追蹤**：完整的操作記錄和審計日誌

## 結論

**利潤數字不是純粹的顯示數字，而是基於實際交易動態計算且可以動用的獨立金額。**系統提供了完整的利潤計算、提款和追蹤機制，確保財務數據的準確性和可操作性。

