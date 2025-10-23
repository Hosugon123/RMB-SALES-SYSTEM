# 利潤同步修復摘要

## 問題描述

系統中有三個利潤數字沒有同步：
1. **儀表板數字**: NT$ 53,011
2. **利潤管理的利潤總額**: NT$ 47,210.80
3. **利潤更動紀錄的利潤餘額**: NT$ 53,015.80

## 根本原因分析

通過分析利潤更動紀錄，發現從 2025/10/21 開始餘額計算出現錯誤。主要問題：

1. **利潤更動紀錄餘額計算錯誤**: 
   - 原系統使用當前總利潤作為基準，倒推每筆記錄的餘額
   - 這導致歷史記錄的餘額不正確

2. **計算邏輯不一致**:
   - 儀表板使用 FIFO 計算所有銷售利潤，然後扣除提款
   - 利潤更動紀錄沒有正確累積計算每筆交易後的餘額

## 正確計算邏輯

根據利潤更動紀錄，正確的計算應該是：

```
基準（2025/10/20 下午2:57:36）: 47,210.80
+ 5,219.00 (2025/10/21 12:22:27 售出利潤:胡) = 52,429.80
+ 5,219.00 (2025/10/21 12:28:52 售出利潤:小曾) = 57,648.80
+ 100.00 (2025/10/21 12:41:21 售出利潤:小曾) = 57,748.80
+ 5.00 (2025/10/21 12:44:41 售出利潤:胡) = 57,753.80
```

**正確的利潤總額應該是: NT$ 57,753.80**

## 修復方案

### 1. 修改 `api_profit_history` 函數 (app.py)

**修改位置**: app.py 第 6194-6294 行

**主要改動**:
- 獲取所有利潤記錄並按時間正序排列
- 從0開始，按時間順序累積計算每筆記錄的餘額
- 利潤入庫時：`餘額 += 金額`
- 利潤提款時：`餘額 -= 金額`
- 將正確的餘額更新到資料庫的 `profit_before` 和 `profit_after` 欄位
- 確保前端顯示的餘額與資料庫一致

**修改前邏輯**:
```python
if balance_before is None or balance_after is None:
    if entry.entry_type == "PROFIT_EARNED":
        balance_after = current_total_profit
        balance_before = balance_after - entry.amount
    elif entry.entry_type == "PROFIT_WITHDRAW":
        balance_before = current_total_profit + abs(entry.amount)
        balance_after = current_total_profit
```

**修改後邏輯**:
```python
# 按時間順序累積計算
running_balance = 0.0
for entry in all_profit_entries_ordered:
    balance_before = running_balance
    if is_withdrawal:
        balance_after = running_balance - abs(entry.amount)
    else:
        balance_after = running_balance + abs(entry.amount)
    running_balance = balance_after
```

### 2. 創建測試頁面

創建了 `test_profit_sync.html` 用於測試和驗證修復結果：
- 對比三個利潤數字
- 顯示利潤更動紀錄
- 顯示診斷信息

### 3. 創建修復腳本

創建了 `fix_profit_calculation.py` 用於一次性修復所有歷史數據：
- 使用 FIFO 計算所有銷售記錄的利潤
- 扣除所有利潤提款
- 計算正確的最終利潤
- 更新 `LedgerEntry` 中的 `profit_before`、`profit_after`、`profit_change` 欄位
- 更新 `CashAccount` 中的 `profit_balance` 欄位

## 驗證步驟

1. **啟動本機測試**:
   ```bash
   python app.py
   ```

2. **打開測試頁面**:
   ```
   http://localhost:5000/test_profit_sync.html
   ```

3. **檢查三個數字是否一致**:
   - 儀表板/總利潤API
   - 利潤管理總額（使用相同API）
   - 利潤更動紀錄餘額

4. **檢查利潤更動紀錄**:
   - 每筆記錄的餘額應該正確累積
   - 最新記錄的餘額應該等於總利潤

## 統一的利潤計算公式

**系統唯一正確的利潤計算公式**:
```
總利潤 = Σ(所有銷售記錄的FIFO利潤) - Σ(所有利潤提款)
```

**利潤更動紀錄的餘額計算**:
```
從最早的記錄開始，按時間順序：
- 初始餘額 = 0
- 每筆利潤入庫: 新餘額 = 舊餘額 + 利潤金額
- 每筆利潤提款: 新餘額 = 舊餘額 - 提款金額
```

## 注意事項

1. **不要修改 FIFO 計算邏輯**: FIFO 是正確的成本計算方法，不應更改
2. **確保時間順序**: 利潤更動紀錄必須按時間正序處理
3. **正負號統一**: 
   - 利潤入庫顯示為正數
   - 利潤提款顯示為負數
   - 資料庫中提款記錄的 amount 為負數
4. **同步更新**: 每次利潤變動時，同時更新三個地方的數字

## 後續維護

1. **每次新增銷售記錄時**: 自動更新利潤餘額
2. **每次利潤提款時**: 正確記錄 `profit_before`、`profit_after`、`profit_change`
3. **定期驗證**: 使用測試頁面檢查三個數字是否一致
4. **避免手動修改**: 不要直接修改資料庫中的利潤相關欄位

## 修復完成檢查清單

- [x] 修改 `api_profit_history` 函數，使用正確的累積計算邏輯
- [x] 創建測試頁面 `test_profit_sync.html`
- [x] 創建修復腳本 `fix_profit_calculation.py`
- [ ] 運行修復腳本修復歷史數據
- [ ] 在測試環境驗證修復結果
- [ ] 部署到生產環境
- [ ] 在生產環境驗證修復結果

## 預期結果

修復完成後，三個利潤數字應該完全一致，都顯示為 **NT$ 57,753.80**（或基於實際數據的正確值）。

