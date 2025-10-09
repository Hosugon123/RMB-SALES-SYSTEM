# 修復7773支付寶帳戶多餘4.28 RMB指南

## 問題描述
- 7773支付寶帳戶原本餘額為0
- 錯誤刪除買入記錄時，RMB沒有正確回滾
- 現在多出了4.28 RMB

## 修復方案

### 方案一：使用修復腳本（推薦）

1. **上傳修復腳本到線上服務器**
   ```bash
   # 上傳 fix_7773_4_28_rmb.py 到線上服務器
   ```

2. **執行修復腳本**
   ```bash
   python fix_7773_4_28_rmb.py
   ```

3. **按照提示操作**
   - 輸入資料庫路徑
   - 確認修復操作

### 方案二：手動SQL修復

1. **備份資料庫**
   ```bash
   cp your_database.db your_database_backup.db
   ```

2. **查找7773支付寶帳戶**
   ```sql
   SELECT ca.id, ca.name, ca.balance, h.name as holder_name
   FROM cash_accounts ca
   LEFT JOIN holders h ON ca.holder_id = h.id
   WHERE ca.currency = 'RMB' 
   AND h.name LIKE '%7773%';
   ```

3. **檢查FIFO庫存**
   ```sql
   SELECT SUM(fi.remaining_rmb) as total_fifo_rmb
   FROM fifo_inventory fi
   JOIN purchase_records pr ON fi.purchase_record_id = pr.id
   WHERE pr.deposit_account_id = <帳戶ID>;
   ```

4. **執行修復**
   ```sql
   BEGIN TRANSACTION;
   UPDATE cash_accounts SET balance = <正確餘額> WHERE id = <帳戶ID>;
   COMMIT;
   ```

5. **驗證修復結果**
   ```sql
   SELECT id, name, balance FROM cash_accounts WHERE id = <帳戶ID>;
   ```

### 方案三：透過管理後台修復

1. **登入管理後台**
2. **到現金管理頁面**
3. **找到7773支付寶帳戶**
4. **手動調整餘額**
   - 將餘額從4.28調整為0（或正確的FIFO庫存值）

## 修復後驗證

1. **檢查帳戶餘額**
   - 7773支付寶帳戶餘額應該為0（或與FIFO庫存一致）

2. **測試刪除功能**
   - 創建一筆測試買入記錄
   - 刪除該記錄
   - 確認RMB帳戶餘額正確回滾

## 預防措施

1. **部署修復後的程式碼**
   ```bash
   git add app.py
   git commit -m "修復買入記錄刪除回滾機制"
   git push origin main
   ```

2. **重啟服務**

3. **測試刪除功能**

## 注意事項

- 修復前務必備份資料庫
- 確認7773支付寶帳戶確實多出了4.28 RMB
- 修復後測試刪除功能確保不再出現問題
