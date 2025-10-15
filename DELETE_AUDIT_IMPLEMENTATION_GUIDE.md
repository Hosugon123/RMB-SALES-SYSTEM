# 刪除記錄審計功能實現指南

## 功能概述

本系統新增了完整的刪除記錄審計功能，可以追蹤所有刪除操作，包括：
- 買入記錄刪除
- 銷售記錄刪除
- 刷卡記錄刪除
- FIFO庫存刪除
- 其他資料刪除

## 已實現的功能

### 1. 資料表模型
- `DeleteAuditLog` - 刪除記錄審計表
- 記錄被刪除記錄的完整資料
- 包含操作者、時間、IP等審計資訊

### 2. 審計服務
- `DeleteAuditService` - 刪除記錄審計服務類
- 自動記錄刪除操作
- 提供查詢和檢索功能

### 3. 管理頁面
- `/admin/delete_audit_logs` - 完整的刪除記錄審計頁面
- 支援篩選、分頁、詳細查看

### 4. API接口
- `/api/delete_audit_logs` - 獲取刪除記錄的API
- 支援篩選和限制數量

### 5. 可重用組件
- `_delete_audit_block.html` - 可開關的刪除記錄審計區塊
- 可在任何頁面中嵌入使用

## 如何在頁面中添加刪除記錄審計區塊

### 方法一：在現有頁面添加（推薦）

在任何頁面的 `{% endblock %}` 之前添加以下代碼：

```html
<!-- 刪除記錄審計區塊 -->
{% if current_user.is_admin %}
{% include '_delete_audit_block.html' %}
{% endif %}
```

### 方法二：手動添加完整代碼

如果需要在自定義頁面中使用，可以複製 `_delete_audit_block.html` 的內容。

## 已添加審計區塊的頁面

1. **買入頁面** (`/buy-in`)
   - 文件：`templates/buy_in.html`
   - 功能：追蹤買入記錄的刪除操作

2. **現金管理頁面** (`/admin/cash_management`)
   - 文件：`templates/cash_management.html`
   - 功能：追蹤帳戶和現金相關的刪除操作

## 建議添加審計區塊的頁面

以下頁面建議也添加刪除記錄審計區塊：

### 1. 銷售頁面 (`/sales-entry`)
```html
<!-- 在 templates/sales_entry.html 的結尾添加 -->
{% if current_user.is_admin %}
{% include '_delete_audit_block.html' %}
{% endif %}
```

### 2. FIFO庫存頁面 (`/fifo-inventory`)
```html
<!-- 在 templates/fifo_inventory.html 的結尾添加 -->
{% if current_user.is_admin %}
{% include '_delete_audit_block.html' %}
{% endif %}
```

### 3. 刷卡記帳頁面 (`/card-purchase`)
```html
<!-- 在 templates/card_purchase.html 的結尾添加 -->
{% if current_user.is_admin %}
{% include '_delete_audit_block.html' %}
{% endif %}
```

### 4. 管理員儀表板 (`/admin/dashboard`)
```html
<!-- 在 templates/admin/dashboard.html 的結尾添加 -->
{% if current_user.is_admin %}
{% include '_delete_audit_block.html' %}
{% endif %}
```

## 審計區塊功能說明

### 1. 預設狀態
- **常閉**：審計區塊預設為收起狀態
- **可開關**：點擊標題欄可以展開/收起
- **僅管理員可見**：只有管理員可以看到審計區塊

### 2. 篩選功能
- **資料表篩選**：可以按資料表類型篩選
- **操作者篩選**：可以按操作者篩選
- **數量限制**：可以設定顯示的記錄數量

### 3. 顯示資訊
- **記錄類型**：買入記錄、銷售記錄、刷卡記錄等
- **操作類型**：回滾買入、回滾銷售、刪除等
- **操作者**：執行刪除操作的使用者
- **時間**：刪除操作的時間
- **描述**：操作的詳細描述

### 4. 快速操作
- **查看詳細**：點擊記錄可以查看完整資料
- **完整頁面**：點擊按鈕跳轉到完整的審計頁面

## 資料庫遷移

執行以下命令來創建審計表：

```bash
# 創建遷移檔案
flask db revision --autogenerate -m "add delete audit logs table"

# 執行遷移
flask db upgrade
```

或者直接使用提供的遷移檔案：
```bash
# 複製遷移檔案到 migrations/versions/ 目錄
cp migrations/versions/add_delete_audit_logs_table.py migrations/versions/

# 執行遷移
flask db upgrade
```

## 測試建議

### 1. 基本功能測試
1. 執行一次買入記錄刪除
2. 檢查審計區塊是否顯示該記錄
3. 驗證記錄的完整性

### 2. 篩選功能測試
1. 測試按資料表篩選
2. 測試按操作者篩選
3. 測試數量限制功能

### 3. 權限測試
1. 使用非管理員帳號登入
2. 確認看不到審計區塊
3. 使用管理員帳號確認可以看到

## 注意事項

### 1. 效能考量
- 審計記錄會持續累積，建議定期清理舊記錄
- 可以考慮設置自動清理策略（如保留最近6個月的記錄）

### 2. 儲存空間
- 審計記錄包含完整的被刪除資料
- 建議監控資料庫大小，必要時實施清理策略

### 3. 安全性
- 審計記錄包含敏感資料，確保只有管理員可以查看
- 考慮對審計記錄進行備份

## 擴展功能建議

### 1. 資料恢復
- 可以基於審計記錄實現資料恢復功能
- 提供「撤銷刪除」操作

### 2. 報表功能
- 生成刪除操作的統計報表
- 按時間、操作者等維度分析

### 3. 通知功能
- 重要刪除操作的自動通知
- 異常刪除模式的警報

## 故障排除

### 1. 審計區塊不顯示
- 確認使用者是管理員
- 檢查模板是否正確包含
- 檢查JavaScript控制台是否有錯誤

### 2. 審計記錄不完整
- 檢查刪除操作是否正確調用審計服務
- 檢查資料庫連接是否正常
- 檢查審計服務的錯誤日誌

### 3. 效能問題
- 檢查審計表的索引是否正確創建
- 考慮增加資料庫查詢的優化
- 檢查是否載入了過多記錄

## 聯繫支援

如果在實現過程中遇到問題，請：
1. 檢查錯誤日誌
2. 確認所有依賴都已正確安裝
3. 聯繫技術支援團隊

