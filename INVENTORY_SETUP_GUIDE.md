# 庫存管理系統安裝指南

## 系統要求

### 基本要求
- Python 3.7+
- Flask 2.0+
- SQLAlchemy 1.4+
- 支持事務的數據庫（MySQL, PostgreSQL, SQLite）

### 推薦配置
- Python 3.9+
- Flask 2.3+
- SQLAlchemy 2.0+
- MySQL 8.0+ 或 PostgreSQL 13+

## 安裝步驟

### 步驟1: 檢查現有系統
確保您的RMB銷售系統已經安裝並運行：
```bash
# 檢查Python版本
python --version

# 檢查Flask版本
python -c "import flask; print(flask.__version__)"

# 檢查系統是否運行
curl http://localhost:5000/
```

### 步驟2: 備份現有數據
在安裝新功能前，建議備份現有數據：
```bash
# 備份數據庫
python backup_database.py

# 或者手動備份
cp your_database.db your_database_backup.db
```

### 步驟3: 創建必要的數據庫表
運行以下腳本創建庫存管理相關的表：

```bash
# 創建庫存日誌表
python create_inventory_logs_table.py

# 或者手動執行SQL
sqlite3 your_database.db < inventory_tables.sql
```

### 步驟4: 更新主應用程序
在 `app.py` 中註冊庫存管理藍圖：

```python
# 在文件頂部添加導入
from inventory_management_api import inventory_bp

# 在 create_app() 函數中註冊藍圖
def create_app():
    app = Flask(__name__)
    # ... 其他配置 ...
    
    # 註冊庫存管理藍圖
    app.register_blueprint(inventory_bp)
    
    # ... 其他藍圖註冊 ...
    return app
```

### 步驟5: 更新導航菜單
在 `templates/base.html` 中添加庫存管理頁面連結：

```html
<!-- 在導航菜單中添加 -->
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('inventory.inventory_management') }}">
        <i class="bi bi-box-seam"></i> 庫存管理
    </a>
</li>
```

### 步驟6: 檢查依賴項
確保所有必要的Python包已安裝：

```bash
pip install -r requirements.txt

# 或者手動安裝
pip install flask-sqlalchemy flask-login
```

## 配置說明

### 數據庫配置
確保數據庫支持事務和外鍵約束：

```python
# 在 app.py 中
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# 啟用外鍵約束（SQLite）
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

### 權限配置
確保用戶有適當的權限進行庫存操作：

```python
# 在 models.py 中檢查用戶權限
class User(db.Model, UserMixin):
    # ... 現有代碼 ...
    
    @property
    def can_manage_inventory(self):
        return self.role in ['admin', 'manager', 'operator']
```

## 驗證安裝

### 1. 運行測試腳本
```bash
python test_inventory_system.py
```

### 2. 檢查API端點
```bash
# 檢查庫存狀態API
curl http://localhost:5000/api/inventory/status

# 檢查庫存批次API
curl http://localhost:5000/api/inventory/batches

# 檢查庫存日誌API
curl http://localhost:5000/api/inventory/logs
```

### 3. 瀏覽器測試
1. 訪問庫存管理頁面：`http://localhost:5000/inventory`
2. 檢查頁面是否正常載入
3. 測試各個功能按鈕
4. 檢查模態框是否正常顯示

## 故障排除

### 常見問題

#### 1. 模態框無法顯示
**症狀**: 點擊按鈕後模態框不顯示
**解決方案**: 
- 檢查Bootstrap CSS和JS是否正確載入
- 檢查瀏覽器控制台是否有JavaScript錯誤
- 確認模態框ID是否正確

#### 2. API請求失敗
**症狀**: 頁面顯示"載入失敗"或"網路錯誤"
**解決方案**:
- 檢查Flask應用是否正在運行
- 確認API端點是否正確註冊
- 檢查數據庫連接是否正常

#### 3. 數據庫表不存在
**症狀**: 出現"表不存在"錯誤
**解決方案**:
- 運行數據庫表創建腳本
- 檢查數據庫連接字符串
- 確認數據庫用戶有創建表的權限

#### 4. 權限不足
**症狀**: 出現"權限不足"或"未授權"錯誤
**解決方案**:
- 檢查用戶是否已登入
- 確認用戶角色是否有權限
- 檢查Flask-Login配置

### 調試方法

#### 1. 檢查Flask日誌
```bash
# 啟動Flask時啟用調試模式
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

#### 2. 檢查瀏覽器控制台
- 按F12打開開發者工具
- 查看Console標籤中的錯誤信息
- 查看Network標籤中的請求狀態

#### 3. 檢查數據庫
```bash
# SQLite
sqlite3 your_database.db ".tables"
sqlite3 your_database.db "SELECT * FROM inventory_logs LIMIT 5;"

# MySQL
mysql -u username -p database_name -e "SHOW TABLES;"
mysql -u username -p database_name -e "SELECT * FROM inventory_logs LIMIT 5;"
```

## 性能優化

### 1. 數據庫索引
為常用查詢添加索引：

```sql
-- 庫存日誌表索引
CREATE INDEX idx_inventory_logs_batch_id ON inventory_logs(batch_id);
CREATE INDEX idx_inventory_logs_operation_type ON inventory_logs(operation_type);
CREATE INDEX idx_inventory_logs_created_at ON inventory_logs(created_at);

-- FIFO庫存表索引
CREATE INDEX idx_fifo_inventory_remaining_rmb ON fifo_inventory(remaining_rmb);
CREATE INDEX idx_fifo_inventory_purchase_date ON fifo_inventory(purchase_date);
```

### 2. 查詢優化
- 使用分頁查詢避免載入過多數據
- 實現數據緩存減少數據庫查詢
- 使用異步載入提升用戶體驗

### 3. 前端優化
- 實現虛擬滾動處理大量數據
- 使用防抖處理頻繁的用戶輸入
- 實現離線功能減少網路依賴

## 安全考慮

### 1. 輸入驗證
- 所有用戶輸入都經過驗證
- 使用參數化查詢防止SQL注入
- 驗證文件上傳類型和大小

### 2. 權限控制
- 實現基於角色的訪問控制
- 記錄所有敏感操作
- 定期審計用戶權限

### 3. 數據保護
- 敏感數據加密存儲
- 定期備份重要數據
- 實現數據恢復機制

## 維護和更新

### 1. 定期檢查
- 檢查系統日誌
- 監控數據庫性能
- 驗證數據一致性

### 2. 備份策略
- 每日自動備份
- 定期測試恢復流程
- 異地備份重要數據

### 3. 版本更新
- 關注安全更新
- 測試新功能
- 制定回滾計劃

## 聯繫支持

如果在安裝過程中遇到問題：

1. **檢查文檔**: 查看本指南和相關文檔
2. **查看日誌**: 檢查系統和應用日誌
3. **運行測試**: 使用提供的測試腳本
4. **尋求幫助**: 聯繫技術支持或社區論壇

---

*最後更新: 2024年12月*
*版本: 1.0*
