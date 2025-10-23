# 售出訂單建立調試系統

## 🚨 問題現狀

用戶建立售出訂單後，只記錄了利潤入庫，但沒有在售出頁面顯示訂單記錄。為了快速診斷問題，我建立了完整的調試系統。

## 🔧 已建立的調試機制

### 1. 詳細的日誌記錄 (app.py)

在 `sales_action` 路由中添加了完整的調試日誌：

```python
print(f"🔍 DEBUG: 收到sales_action請求，action={action}")
print(f"🔍 DEBUG: 表單數據: {dict(request.form)}")
print(f"🔍 DEBUG: 客戶信息 - customer_name={customer_name}, customer_id={customer_id}")
print(f"🔍 DEBUG: 銷售數據 - RMB={rmb}, 匯率={rate}, 台幣={twd}")
print(f"🔍 DEBUG: 創建SalesRecord:")
print(f"  客戶ID: {new_sale.customer_id}")
print(f"  RMB帳戶ID: {new_sale.rmb_account_id}")
print(f"  是否結清: {new_sale.is_settled}")
print(f"✅ DEBUG: 資料庫提交成功")
```

### 2. 售出訂單檢查腳本 (sales_order_debug.py)

創建了專門的檢查腳本，可以：
- 檢查最新的售出記錄
- 檢查未結清的售出記錄
- 檢查利潤記錄
- 檢查資料庫約束完整性
- 測試售出訂單建立過程

### 3. 測試頁面 (test_sales_creation.html)

創建了專門的測試頁面，可以：
- 模擬售出訂單建立
- 顯示詳細的調試信息
- 實時查看服務器響應
- 自動獲取可用的RMB帳戶

## 🧪 使用方法

### 1. 啟動調試模式
```bash
python app.py
```

### 2. 打開測試頁面
```
http://localhost:5000/test_sales_creation.html
```

### 3. 填寫測試表單
- 客戶名稱: 測試客戶
- 售出金額: 1000 RMB
- 售出匯率: 4.5
- 訂單日期: 2025-10-23
- 選擇RMB出貨帳戶

### 4. 點擊建立測試訂單

### 5. 查看調試信息
- 測試結果會顯示在頁面上
- 詳細的調試信息會顯示在調試區域
- 服務器控制台會顯示完整的日誌

## 🔍 調試檢查點

### 1. 表單數據檢查
- 確認所有必需欄位都有值
- 確認數據類型正確
- 確認RMB帳戶ID存在

### 2. 客戶處理檢查
- 確認客戶查找或創建成功
- 確認客戶ID正確設置

### 3. 銷售記錄創建檢查
- 確認所有欄位都正確設置
- 確認 `is_settled=False`
- 確認 `rmb_account_id` 設置
- 確認 `operator_id` 設置

### 4. 資料庫操作檢查
- 確認記錄成功添加到資料庫
- 確認FIFO庫存分配成功
- 確認利潤計算成功
- 確認資料庫提交成功

### 5. 驗證檢查
- 確認記錄在資料庫中能找到
- 確認記錄在未結清查詢中能找到
- 確認售出頁面能顯示記錄

## 📊 預期調試輸出

正常情況下，控制台應該顯示：

```
🔍 DEBUG: 收到sales_action請求，action=create_order
🔍 DEBUG: 表單數據: {'customer_name': '測試客戶', 'rmb_sell_amount': '1000.0', ...}
🔍 DEBUG: 客戶信息 - customer_name=測試客戶, customer_id=None
🔍 DEBUG: 通過名稱找到客戶: 測試客戶
🔍 DEBUG: 銷售數據 - RMB=1000.0, 匯率=4.5, 台幣=4500.0
🔍 DEBUG: 找到RMB帳戶: 測試RMB帳戶
🔍 DEBUG: 創建SalesRecord:
  客戶ID: 1
  RMB帳戶ID: 1
  是否結清: False
🔍 DEBUG: SalesRecord已添加到資料庫
🔍 DEBUG: SalesRecord ID已獲取: 123
🔍 DEBUG: FIFO庫存分配完成
🔍 DEBUG: 利潤計算結果: {'profit_twd': 500.0, ...}
🔍 DEBUG: 計算到利潤 500.0 TWD
🔍 DEBUG: 利潤記錄結果: {'success': True, ...}
✅ DEBUG: 資料庫提交成功
✅ DEBUG: 驗證成功，售出記錄已保存:
  ID: 123
  客戶: 測試客戶
  RMB帳戶: 測試RMB帳戶
  是否結清: False
```

## ❌ 常見錯誤模式

### 1. 表單數據問題
```
❌ ERROR: RMB出貨帳戶為空
❌ ERROR: 找不到RMB帳戶 ID 1
```

### 2. 客戶處理問題
```
❌ ERROR: 無法找到或創建客戶
```

### 3. 資料庫操作問題
```
❌ ERROR: 庫存分配或利潤計算失敗: ...
❌ ERROR: 售出記錄保存後找不到
```

## 🚀 下一步操作

1. **重新啟動應用**:
   ```bash
   python app.py
   ```

2. **打開測試頁面**:
   ```
   http://localhost:5000/test_sales_creation.html
   ```

3. **建立測試訂單**:
   - 填寫表單
   - 點擊建立測試訂單
   - 查看調試信息

4. **檢查售出頁面**:
   ```
   http://localhost:5000/sales-entry
   ```
   - 確認新訂單是否顯示

5. **分析調試輸出**:
   - 查看控制台日誌
   - 識別問題所在
   - 根據錯誤信息進行修復

## 📋 調試檢查清單

- [ ] 表單數據完整
- [ ] 客戶查找/創建成功
- [ ] RMB帳戶驗證通過
- [ ] SalesRecord創建成功
- [ ] 所有欄位正確設置
- [ ] 資料庫添加成功
- [ ] FIFO庫存分配成功
- [ ] 利潤計算成功
- [ ] 資料庫提交成功
- [ ] 記錄驗證通過
- [ ] 售出頁面顯示記錄

現在系統會提供詳細的調試信息，幫助我們快速定位問題所在！
