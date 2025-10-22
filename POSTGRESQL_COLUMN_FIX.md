# PostgreSQL 欄位修復解決方案

## 🎯 問題根本原因

**錯誤訊息：**
```
column "from_account_id" of relation "ledger_entries" does not exist
```

**根本原因：** 線上PostgreSQL資料庫的`ledger_entries`表格缺少以下欄位：
- `from_account_id` (INTEGER)
- `to_account_id` (INTEGER) 
- `profit_before` (REAL)
- `profit_after` (REAL)
- `profit_change` (REAL)

這些欄位在本地SQLite中存在，但PostgreSQL中沒有，導致銷帳API創建LedgerEntry時失敗。

## 🔧 修復方案

### 1. 自動欄位修復函數

在`app.py`中添加了`fix_postgresql_columns()`函數：

```python
def fix_postgresql_columns():
    """修復PostgreSQL缺少的欄位"""
    try:
        # 檢查是否為PostgreSQL
        database_url = str(db.engine.url)
        if 'postgresql' not in database_url:
            return True
        
        print("🔧 檢查PostgreSQL欄位...")
        
        # 檢查ledger_entries表格欄位
        columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ledger_entries' 
            AND table_schema = 'public'
            AND column_name IN ('from_account_id', 'to_account_id', 'profit_before', 'profit_after', 'profit_change')
        """)
        
        result = db.session.execute(columns_query).fetchall()
        existing_columns = [row[0] for row in result]
        
        # 需要添加的欄位
        columns_to_add = [
            ('from_account_id', 'INTEGER'),
            ('to_account_id', 'INTEGER'),
            ('profit_before', 'REAL'),
            ('profit_after', 'REAL'),
            ('profit_change', 'REAL')
        ]
        
        missing_columns = [col for col, _ in columns_to_add if col not in existing_columns]
        
        if missing_columns:
            print(f"🔧 發現缺少欄位: {missing_columns}，正在修復...")
            
            for column_name, column_type in columns_to_add:
                if column_name in missing_columns:
                    try:
                        alter_query = text(f"""
                            ALTER TABLE ledger_entries 
                            ADD COLUMN {column_name} {column_type}
                        """)
                        db.session.execute(alter_query)
                        db.session.commit()
                        print(f"✅ 添加欄位: {column_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                            print(f"ℹ️ 欄位已存在: {column_name}")
                        else:
                            print(f"❌ 添加欄位 {column_name} 失敗: {e}")
                            db.session.rollback()
        else:
            print("✅ PostgreSQL欄位檢查通過")
        
        return True
        
    except Exception as e:
        print(f"⚠️ PostgreSQL欄位修復失敗: {e}")
        return False
```

### 2. 應用程式啟動時自動修復

在`app.py`的啟動部分添加了自動修復：

```python
if __name__ == "__main__":
    # 啟動時修復PostgreSQL欄位
    with app.app_context():
        fix_postgresql_columns()
    app.run(debug=True)
```

### 3. 銷帳API中即時修復

在銷帳API創建LedgerEntry之前添加欄位檢查：

```python
# 確保PostgreSQL欄位存在
fix_postgresql_columns()

settlement_entry = LedgerEntry(
    account_id=account.id,
    entry_type="SETTLEMENT",
    amount=amount,
    entry_date=datetime.utcnow(),
    description=f"客戶「{customer.name}」銷帳收款 - {note}" if note else f"客戶「{customer.name}」銷帳收款",
    operator_id=operator_id
)
```

## 📋 修復步驟

### 1. 立即修復（已實施）

1. ✅ 添加了`fix_postgresql_columns()`函數
2. ✅ 在應用程式啟動時自動修復
3. ✅ 在銷帳API中添加即時修復
4. ✅ 創建了測試腳本

### 2. 部署步驟

1. **提交代碼變更**
   ```bash
   git add .
   git commit -m "修復PostgreSQL欄位問題"
   git push origin main
   ```

2. **等待Render自動部署**
   - Render會自動檢測到代碼變更
   - 重新構建和部署應用程式
   - 啟動時會自動修復欄位

3. **驗證修復結果**
   - 使用`test_postgresql_fix.py`測試
   - 檢查銷帳功能是否正常

## 🧪 測試工具

### 1. 本地測試
```bash
python test_postgresql_fix.py
```

### 2. 手動測試
訪問線上環境並嘗試銷帳操作

### 3. 日誌檢查
在Render Dashboard中查看服務日誌，確認欄位修復成功

## 🔍 預期結果

修復成功後，應該看到以下日誌：

```
🔧 檢查PostgreSQL欄位...
🔧 發現缺少欄位: ['from_account_id', 'to_account_id', 'profit_before', 'profit_after', 'profit_change']，正在修復...
✅ 添加欄位: from_account_id
✅ 添加欄位: to_account_id
✅ 添加欄位: profit_before
✅ 添加欄位: profit_after
✅ 添加欄位: profit_change
```

## 🚀 部署後驗證

1. **檢查應用程式狀態**
   - 確認應用程式正常啟動
   - 查看啟動日誌中的欄位修復訊息

2. **測試銷帳功能**
   - 嘗試進行銷帳操作
   - 確認不再出現欄位錯誤

3. **檢查資料庫結構**
   - 確認`ledger_entries`表格包含所有必要欄位

## 📝 注意事項

1. **一次性修復**：欄位修復只需要執行一次，之後會自動跳過
2. **向後兼容**：修復不會影響現有數據
3. **自動化**：每次應用程式啟動都會檢查，確保欄位存在
4. **錯誤處理**：如果欄位已存在，會自動跳過而不會報錯

## 🎉 預期效果

修復完成後：
- ✅ 銷帳API不再出現500錯誤
- ✅ 可以正常創建LedgerEntry記錄
- ✅ 所有銷帳功能恢復正常
- ✅ 系統穩定運行

這個修復方案解決了PostgreSQL和SQLite之間資料庫結構不同步的根本問題，確保系統在線上環境中正常運行。
