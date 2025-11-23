# 帳戶餘額計算算法完整列表

## 算法1：實際運作時的帳戶餘額變動（從代碼中）

### 買入時（app.py 5252行）：
```python
deposit_account.balance += rmb_amount
```
**邏輯：** 買入時，RMB帳戶餘額增加

### 售出時（app.py 994行）：
```python
deduction_account.balance -= rmb_amount
```
**邏輯：** 售出時，從指定的扣款帳戶扣款（不管庫存來源）

### 提款時（app.py 6202行）：
```python
account.balance -= amount
```
**邏輯：** 提款時，帳戶餘額減少

### 轉帳時：
```python
from_account.balance -= amount
to_account.balance += amount
```
**邏輯：** 轉帳時，轉出帳戶減少，轉入帳戶增加

---

## 算法2：數據修復API中的計算（app.py 12072-12097行）

### 當前邏輯：
```python
# 從該帳戶庫存實際售出的金額
actual_sold_from_this_account = SUM(FIFOSalesAllocation.allocated_rmb)
  WHERE FIFOInventory.purchase_record.deposit_account_id == account.id

# 帳戶餘額
new_balance = deposit_amount - actual_sold_from_this_account
```

**問題：**
- 使用"從該帳戶庫存實際售出"，但實際運作時是"從該帳戶扣款的售出"
- 這會導致計算結果與實際運作不一致

---

## 算法3：修復腳本中的計算（fix_account_balance_exclude_ledger.py）

### 當前邏輯：
```python
# 從該帳戶庫存實際售出的金額
actual_sold_from_this_account = SUM(FIFOSalesAllocation.allocated_rmb)
  WHERE FIFOInventory.purchase_record.deposit_account_id == account.id

# 帳戶餘額
new_balance = deposit_amount - actual_sold_from_this_account
```

**問題：**
- 與算法2相同
- 與實際運作邏輯不一致

---

## 算法4：根據業務邏輯的正確計算

### 根據您提供的業務邏輯：
```
帳戶餘額 = 該帳戶作為deposit_account的買入 - 該帳戶作為rmb_account的售出扣款
```

### 代碼實現：
```python
deposit_amount = SUM(PurchaseRecord.rmb_amount)
  WHERE PurchaseRecord.deposit_account_id == account.id

sales_deduction = SUM(SalesRecord.rmb_amount)
  WHERE SalesRecord.rmb_account_id == account.id

new_balance = deposit_amount - sales_deduction
```

**這才是正確的！** 因為：
- 買入時：餘額增加
- 售出時：從指定帳戶扣款（不管庫存來源）
- 帳戶餘額反映的是"該帳戶實際擁有的金額"

---

## 算法5：模擬計算（按時間順序累積）

### 邏輯：
```python
balance = 0
for each operation in chronological_order:
    if operation.type == 'PURCHASE':
        balance += operation.amount
    elif operation.type == 'SALE':
        balance -= operation.amount
    elif operation.type == 'DEPOSIT':
        balance += operation.amount
    elif operation.type == 'WITHDRAW':
        balance -= operation.amount
    # ... 其他操作
```

**這應該等於當前餘額**（如果沒有記錄被刪除）

---

## 問題分析

### 從檢查結果看：

1. **當前餘額 = 方法1（買入 - 售出扣款）**
   - 這表示帳戶餘額是通過實際操作累積的
   - 這是正確的！

2. **但用戶說"帳面金額不符合實務金額"**
   - 這可能意味著：歷史數據有問題
   - 或者：有記錄被刪除但餘額未正確回滾
   - 或者：有其他未記錄的操作

3. **不應該直接計算**
   - 不應該用"買入 - 售出扣款"直接計算
   - 應該保持當前的餘額（因為它是通過實際操作累積的）
   - 或者：需要檢查是否有記錄被刪除，需要回滾餘額

---

## 正確的修復方式

### 選項1：保持當前餘額（如果它是通過實際操作累積的）

**邏輯：**
- 當前餘額已經是通過實際操作累積的
- 不應該重新計算
- 只需要確保未來操作正確

### 選項2：檢查並修復歷史數據問題

**邏輯：**
- 檢查是否有記錄被刪除但餘額未回滾
- 檢查是否有其他未記錄的操作
- 修復這些問題後，重新計算餘額

### 選項3：使用正確的計算方式（如果確認歷史數據正確）

**邏輯：**
```python
帳戶餘額 = 買入 - 售出扣款
```
- 這與實際運作邏輯一致
- 但前提是歷史數據正確

---

## 建議

**根據您的描述"帳面金額不符合實務金額"，我建議：**

1. **先檢查歷史數據**
   - 是否有記錄被刪除？
   - 是否有其他未記錄的操作？
   - 是否有手動修改的餘額？

2. **確認正確的帳戶餘額應該是多少**
   - 根據實際業務操作記錄
   - 或者根據帳本記錄

3. **然後決定修復方式**
   - 如果歷史數據正確，使用方法1（買入 - 售出扣款）
   - 如果歷史數據有問題，需要先修復歷史數據

