# 買入記錄刪除回滾問題修復指南

## 問題說明

在之前的版本中，刪除買入記錄時的回滾機制有誤：

### 錯誤的回滾邏輯
- ❌ **只處理了純利潤庫存**（手續費）的情況
- ❌ **沒有回滾正常買入記錄的帳戶餘額**

### 正確的回滾邏輯（已修正）
當刪除買入記錄時，應該執行以下回滾：
- ✅ **RMB帳戶減少款項**（刪除買入時增加的RMB）
- ✅ **台幣帳戶回補款項**（退回買入時支付的台幣）

### 影響範圍
如果在線上環境已經執行過買入記錄刪除操作，會導致：
- ✅ RMB帳戶餘額：**正常**（因為沒有扣除，所以RMB還在）
- ❌ 台幣帳戶餘額：**少了應該回補的金額**

---

## 修復方案

提供三種修復方案，請根據您的情況選擇：

### 方案一：使用備份資料庫自動修復（推薦）

如果您有完整的資料庫備份，這是最準確的方案。

#### 步驟

1. **找到最近的備份檔案**
   ```bash
   # 檢查備份目錄
   ls -la ./backups/
   # 或從GCS下載備份
   ```

2. **執行修復分析腳本**
   ```bash
   python fix_purchase_deletion_rollback.py
   ```

3. **按照提示輸入資訊**
   ```
   1. 備份資料庫路徑: ./backups/sales_system_backup_20250109.db
   2. 當前資料庫路徑: ./instance/sales_system.db
   ```

4. **檢查生成的修復SQL**
   
   腳本會生成兩個檔案：
   - `fix_purchase_deletion_YYYYMMDD_HHMMSS.sql` - 修復SQL語句
   - `fix_purchase_deletion_report_YYYYMMDD_HHMMSS.json` - 詳細報告
   
   **修復SQL範例：**
   ```sql
   -- 修復買入記錄錯誤刪除的回滾問題
   -- 生成時間: 2025-01-09 10:30:00
   
   BEGIN TRANSACTION;
   
   -- 修正帳戶: 王小明-台幣 (當前: $50,000.00 -> 修正後: $58,000.00)
   UPDATE cash_accounts SET balance = 58000.00 WHERE id = 5;
   
   -- 修正帳戶: 李大華-台幣 (當前: $120,000.00 -> 修正後: $135,000.00)
   UPDATE cash_accounts SET balance = 135000.00 WHERE id = 8;
   
   COMMIT;
   ```

5. **執行修復SQL**

   **方法A：使用sqlite3命令行**
   ```bash
   # 先備份當前資料庫
   cp instance/sales_system.db instance/sales_system_backup_$(date +%Y%m%d).db
   
   # 執行修復SQL
   sqlite3 instance/sales_system.db < fix_purchase_deletion_20250109_103000.sql
   ```

   **方法B：在線上環境使用Python**
   ```python
   from app import app, db
   
   with app.app_context():
       # 讀取SQL檔案
       with open('fix_purchase_deletion_20250109_103000.sql', 'r') as f:
           sql_statements = f.read()
       
       # 執行SQL（跳過註解和空行）
       for statement in sql_statements.split(';'):
           statement = statement.strip()
           if statement and not statement.startswith('--'):
               db.session.execute(db.text(statement))
       
       db.session.commit()
       print("✅ 修復完成！")
   ```

6. **驗證修復結果**
   
   登入系統檢查相關帳戶餘額是否正確。

---

### 方案二：手動調整帳戶餘額

如果沒有備份或備份不完整，可以手動調整。

#### 步驟

1. **執行手動修復工具**
   ```bash
   python manual_fix_account_balance.py
   ```

2. **查看所有帳戶列表**
   
   工具會顯示所有活躍帳戶及其當前餘額。

3. **選擇需要調整的帳戶**
   
   輸入帳戶ID和調整金額。

4. **示例操作**
   ```
   請輸入帳戶ID: 5
   請輸入調整金額 (正數為增加，負數為減少): 8000
   請輸入調整原因: 修復買入記錄刪除回滾問題
   
   準備調整帳戶: 王小明-台幣 (TWD)
      當前餘額: 50,000.00
      調整金額: +8,000.00
      調整後餘額: 58,000.00
      原因: 修復買入記錄刪除回滾問題
   
   確認執行此調整？(yes/no): yes
   ✅ 帳戶餘額調整完成！
   ```

---

### 方案三：重新部署並使用備份還原

如果問題嚴重且有完整備份，可以考慮還原到備份狀態。

#### 步驟

1. **備份當前資料庫**
   ```bash
   cp instance/sales_system.db instance/sales_system_current_$(date +%Y%m%d).db
   ```

2. **還原備份資料庫**
   ```bash
   cp backups/sales_system_backup_YYYYMMDD.db instance/sales_system.db
   ```

3. **重新執行刪除操作**
   
   使用修復後的程式碼，重新執行需要刪除的買入記錄。

4. **部署修復後的程式碼**
   ```bash
   git add app.py
   git commit -m "修復買入記錄刪除回滾機制"
   git push origin main
   ```

---

## 修復後的程式碼變更

### 修改位置
`app.py` 第 709-747 行

### 修改內容

**之前的錯誤邏輯：**
```python
# 只處理純利潤庫存（手續費）
if (purchase_record.channel is None and 
    purchase_record.payment_account is None and 
    purchase_record.twd_cost == 0):
    # ... 扣除手續費
    pass
# ❌ 沒有處理正常買入記錄的回滾！
```

**修正後的邏輯：**
```python
# 根據買入記錄類型進行不同的處理
if (purchase_record.channel is None and 
    purchase_record.payment_account is None and 
    purchase_record.twd_cost == 0):
    # 純利潤庫存（手續費）：從入庫帳戶中扣除
    # ... 扣除手續費
else:
    # ✅ 正常買入記錄：回滾帳戶餘額
    # RMB帳戶刪除款項（減少RMB餘額）
    if purchase_record.deposit_account:
        deposit_account.balance -= purchase_record.rmb_amount
    
    # 台幣帳戶回補款項（增加台幣餘額）
    if purchase_record.payment_account:
        payment_account.balance += purchase_record.twd_cost
```

---

## 預防措施

為避免未來再次發生類似問題：

### 1. 定期備份
確保資料庫定期備份：
```bash
# 檢查備份配置
cat backup_config.json

# 手動執行備份
python database_backup.py
```

### 2. 測試環境驗證
在線上執行刪除操作前，先在測試環境驗證：
```bash
# 複製線上資料庫到測試環境
cp production/sales_system.db test/sales_system.db

# 在測試環境執行刪除操作
# 檢查帳戶餘額是否正確
```

### 3. 添加操作日誌
考慮在刪除操作時添加詳細日誌：
```python
# 在刪除前記錄
print(f"刪除前 - RMB帳戶餘額: {deposit_account.balance}")
print(f"刪除前 - 台幣帳戶餘額: {payment_account.balance}")

# 執行刪除和回滾
# ...

# 在刪除後記錄
print(f"刪除後 - RMB帳戶餘額: {deposit_account.balance}")
print(f"刪除後 - 台幣帳戶餘額: {payment_account.balance}")
```

---

## 常見問題

### Q1: 如何確認哪些買入記錄被錯誤刪除了？

**A:** 如果有備份，使用方案一的自動分析工具。如果沒有備份，可以：
1. 檢查現金流水記錄（如果有保留）
2. 檢查業務記錄或手寫單據
3. 詢問操作人員最近刪除了哪些記錄

### Q2: 修復後帳戶餘額還是不對怎麼辦？

**A:** 可能的原因：
1. 備份不是最新的 - 使用更新的備份重新分析
2. 有其他問題導致餘額錯誤 - 需要全面審計
3. 修復金額計算錯誤 - 手動驗證計算邏輯

建議使用全局數據同步功能：
```python
from global_sync import sync_entire_database
sync_entire_database(db.session)
```

### Q3: 可以直接修改資料庫餘額嗎？

**A:** 可以，但要注意：
1. 先備份資料庫
2. 記錄修改原因
3. 最好通過工具而不是直接SQL
4. 修改後驗證相關功能

### Q4: RMB帳戶餘額也需要調整嗎？

**A:** 通常不需要。因為之前的錯誤邏輯沒有扣除RMB，所以RMB帳戶餘額是正確的。只需要調整台幣帳戶即可。

---

## 聯絡支援

如果在修復過程中遇到問題，請：

1. 保留所有日誌檔案
2. 記錄詳細的錯誤訊息
3. 備份當前資料庫狀態
4. 聯繫技術支援團隊

---

## 版本記錄

- **2025-01-09**: 初版發布
  - 修復買入記錄刪除回滾機制
  - 提供三種修復方案
  - 創建自動修復工具


