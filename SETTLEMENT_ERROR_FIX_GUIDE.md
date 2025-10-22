# 🛠️ 銷帳功能 500 錯誤修復指南

## 問題描述

線上部署的銷帳功能出現 500 內部伺服器錯誤，具體表現為：
- 用戶嘗試銷帳時出現「伺服器內部錯誤，操作失敗」的錯誤訊息
- 瀏覽器開發者工具顯示 `POST /api/settlement` 返回 500 狀態碼
- 錯誤發生在銷帳 API 端點 `/api/settlement`

## 問題分析

根據代碼檢查，可能的問題原因包括：

### 1. 資料庫結構問題
- `ledger_entries` 表格可能缺少必要欄位
- `cash_logs` 表格可能不存在或結構不完整
- 外鍵約束問題導致資料插入失敗

### 2. 資料庫被自動清空
- 根據歷史記錄，專案中存在多個清空腳本
- 可能被定時任務或自動化腳本清空資料
- 缺少必要的測試資料

### 3. 銷帳 API 邏輯問題
- 在創建 `LedgerEntry` 記錄時遇到欄位不存在的錯誤
- 資料庫事務處理失敗
- 外鍵關聯問題

## 修復方案

### 方案一：使用修復腳本（推薦）

1. **上傳修復腳本到線上服務器**
   ```bash
   # 上傳 fix_settlement_error.py 到線上服務器
   ```

2. **執行修復腳本**
   ```bash
   python fix_settlement_error.py
   ```

3. **修復腳本會自動：**
   - 檢查資料庫表格結構
   - 修復缺失的欄位
   - 創建必要的表格
   - 添加範例測試資料

### 方案二：手動修復

1. **檢查資料庫表格**
   ```sql
   -- 檢查 ledger_entries 表格
   PRAGMA table_info(ledger_entries);
   
   -- 檢查 cash_logs 表格
   PRAGMA table_info(cash_logs);
   ```

2. **修復缺失的欄位**
   ```sql
   -- 添加缺失的欄位到 ledger_entries
   ALTER TABLE ledger_entries ADD COLUMN profit_before FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_after FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN profit_change FLOAT;
   ALTER TABLE ledger_entries ADD COLUMN from_account_id INTEGER;
   ALTER TABLE ledger_entries ADD COLUMN to_account_id INTEGER;
   ```

3. **創建缺失的表格**
   ```sql
   -- 如果 cash_logs 表格不存在
   CREATE TABLE cash_logs (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       time DATETIME DEFAULT CURRENT_TIMESTAMP,
       type VARCHAR(50),
       description VARCHAR(200),
       amount FLOAT,
       operator_id INTEGER NOT NULL,
       FOREIGN KEY (operator_id) REFERENCES user(id)
   );
   ```

### 方案三：重新初始化資料庫

如果資料庫已被清空，需要重新初始化：

1. **備份當前資料庫**
   ```bash
   cp instance/sales_system.db instance/sales_system_backup.db
   ```

2. **運行資料庫遷移**
   ```bash
   flask db upgrade
   ```

3. **添加測試資料**
   ```sql
   -- 插入測試用戶
   INSERT INTO user (username, password_hash, is_admin) 
   VALUES ('admin', 'pbkdf2:sha256:600000$admin$hash', 1);
   
   -- 插入測試客戶
   INSERT INTO customers (name, total_receivables_twd) 
   VALUES ('測試客戶', 1000.00);
   
   -- 插入測試現金帳戶
   INSERT INTO cash_accounts (name, balance, currency, is_active, holder_id) 
   VALUES ('台幣帳戶', 5000.00, 'TWD', 1, 1);
   ```

## 測試修復結果

### 1. 使用測試腳本
```bash
python test_settlement_fix.py
```

### 2. 手動測試
1. 登入系統
2. 進入現金管理頁面
3. 選擇一個客戶進行銷帳
4. 輸入銷帳金額（如 1.00）
5. 選擇收款帳戶
6. 點擊「確認銷帳」
7. 檢查是否出現成功訊息

### 3. 檢查伺服器日誌
查看應用程式日誌，確認沒有錯誤訊息：
```bash
# 查看 Render 服務日誌
# 或檢查應用程式的錯誤日誌
```

## 預防措施

### 1. 禁用自動清空功能
- 檢查是否有定時任務在運行清空腳本
- 移除或重命名 `.DANGER` 擴展名的腳本
- 檢查 Render 的 cron 作業配置

### 2. 加強錯誤處理
- 在銷帳 API 中添加更詳細的錯誤處理
- 記錄詳細的錯誤日誌
- 添加資料庫連接檢查

### 3. 定期備份
- 設置自動資料庫備份
- 定期檢查資料庫完整性
- 監控資料庫大小變化

## 故障排除

### 常見錯誤及解決方法

1. **"from_account_id does not exist"**
   - 解決：運行修復腳本添加缺失欄位

2. **"table ledger_entries doesn't exist"**
   - 解決：運行資料庫遷移或手動創建表格

3. **"database is locked"**
   - 解決：重啟應用程式或檢查資料庫連接

4. **"foreign key constraint failed"**
   - 解決：檢查相關表格的資料完整性

## 聯絡支援

如果修復後仍有問題，請提供以下信息：
1. 完整的錯誤訊息
2. 伺服器日誌截圖
3. 資料庫表格結構信息
4. 測試腳本的執行結果

---

**注意：** 在執行任何修復操作前，請務必備份資料庫！
