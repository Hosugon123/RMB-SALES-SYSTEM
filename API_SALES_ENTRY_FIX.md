# API Sales Entry 參數解析修復摘要

## 🚨 問題描述

`/api/sales-entry` 請求因 "輸入的資料格式不正確" 錯誤而失敗 (400 Bad Request)，這很可能是因為嘗試將空的或無效的字串轉換為 int/float 失敗。

## 🔧 已完成的修復

### 1. 更穩健的參數解析邏輯 (約 2633-2723 行)

**修復前問題**:
```python
# 直接轉換，容易因空字符串或無效格式失敗
rmb_account_id = int(data.get("rmb_account_id"))
rmb_amount = float(data.get("rmb_amount"))
exchange_rate = float(data.get("exchange_rate"))
```

**修復後特點**:

#### A. 安全的字符串參數處理
```python
# 安全地獲取字符串參數，處理空值
customer_id = data.get("customer_id", "").strip() if data.get("customer_id") else ""
customer_name_manual = data.get("customer_name_manual", "").strip() if data.get("customer_name_manual") else ""
```

#### B. 自定義安全轉換函數
```python
def safe_convert_to_int(value, field_name):
    """安全地將值轉換為整數"""
    if not value or value == "":
        return None
    try:
        # 先轉換為字符串，去除空白
        str_value = str(value).strip()
        if not str_value:
            return None
        return int(str_value)
    except (ValueError, TypeError) as e:
        print(f"DEBUG: {field_name} 轉換失敗: '{value}' -> {e}")
        return None

def safe_convert_to_float(value, field_name):
    """安全地將值轉換為浮點數"""
    if not value or value == "":
        return None
    try:
        # 先轉換為字符串，去除空白
        str_value = str(value).strip()
        if not str_value:
            return None
        return float(str_value)
    except (ValueError, TypeError) as e:
        print(f"DEBUG: {field_name} 轉換失敗: '{value}' -> {e}")
        return None
```

#### C. 安全的數值參數轉換
```python
# 使用安全轉換函數
rmb_account_id = safe_convert_to_int(data.get("rmb_account_id"), "rmb_account_id")
rmb_amount = safe_convert_to_float(data.get("rmb_amount"), "rmb_amount")
exchange_rate = safe_convert_to_float(data.get("exchange_rate"), "exchange_rate")
```

#### D. 詳細的驗證邏輯
```python
# 詳細驗證每個欄位，提供具體的錯誤信息
validation_errors = []

if not rmb_account_id:
    validation_errors.append("RMB出貨帳戶")
elif rmb_account_id <= 0:
    validation_errors.append("RMB出貨帳戶ID必須大於0")
    
if not rmb_amount:
    validation_errors.append("售出金額")
elif rmb_amount <= 0:
    validation_errors.append("售出金額必須大於0")
    
if not exchange_rate:
    validation_errors.append("匯率")
elif exchange_rate <= 0:
    validation_errors.append("匯率必須大於0")
```

## 🎯 修復的關鍵點

### 1. 零轉換錯誤
- 所有數值轉換都使用安全的函數
- 空字符串和無效格式不會導致程序崩潰
- 轉換失敗時返回 `None` 而不是拋出異常

### 2. 詳細的錯誤信息
- 每個轉換失敗都有具體的日誌記錄
- 驗證失敗時提供具體的錯誤描述
- 顯示原始數據用於調試

### 3. 完整的參數驗證
- 檢查參數是否存在
- 檢查參數是否為有效數值
- 檢查數值是否在合理範圍內

### 4. 調試友好的日誌
- 每個步驟都有詳細的日誌輸出
- 顯示轉換前後的值
- 記錄驗證過程和結果

## 📊 預期調試輸出

修復後，控制台應該顯示：

```
🔍 DEBUG: 收到api_sales_entry請求，數據: {'customer_id': '1', 'rmb_account_id': '123', 'rmb_amount': '5', 'exchange_rate': '5'}
DEBUG: 開始解析請求參數...
DEBUG: 客戶參數 - customer_id: '1', customer_name_manual: ''
DEBUG: 數值參數 - rmb_account_id: 123, rmb_amount: 5.0, exchange_rate: 5.0
DEBUG: 所有參數驗證通過，開始業務邏輯處理...
```

如果參數有問題，會顯示：

```
DEBUG: rmb_amount 轉換失敗: '' -> invalid literal for int() with base 10: ''
DEBUG: 欄位驗證失敗 - 錯誤: ['售出金額']
DEBUG: 原始數據: {'customer_id': '1', 'rmb_account_id': '123', 'rmb_amount': '', 'exchange_rate': '5'}
```

## 🧪 測試步驟

1. **重新啟動應用**:
   ```bash
   python app.py
   ```

2. **打開售出錄入頁面**:
   ```
   http://localhost:5000/sales-entry
   ```

3. **測試各種情況**:
   - 正常填寫所有欄位
   - 留空某些欄位
   - 輸入無效的數值格式
   - 輸入負數或零

4. **查看控制台日誌**:
   - 檢查參數解析過程
   - 確認錯誤信息是否具體
   - 驗證轉換是否成功

## ✅ 修復驗證

修復完成後，應該看到：

1. **不再出現 "輸入的資料格式不正確" 錯誤**: 所有轉換錯誤都被安全處理
2. **具體的錯誤信息**: 知道哪個欄位有什麼問題
3. **詳細的調試日誌**: 可以追蹤整個參數解析過程
4. **成功的訂單創建**: 當所有參數正確時，訂單能成功創建

## 🚀 下一步

1. 重新啟動本機測試伺服器
2. 測試建立售出訂單
3. 查看控制台調試日誌
4. 確認錯誤信息是否更具體
5. 驗證訂單創建是否成功

現在 `/api/sales-entry` 應該能安全地處理各種參數格式，並提供詳細的錯誤信息幫助診斷問題！
