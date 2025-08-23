# 數據修復 API 修復部署指南

## 🚀 部署步驟

### 1. 提交修復後的代碼到 Git

```bash
# 添加所有修改的文件
git add .

# 提交修復
git commit -m "修復數據修復 API: 添加 traceback 導入、修正字段名稱、增強錯誤處理"

# 推送到遠程倉庫
git push origin main
```

### 2. Render 平台自動部署

一旦代碼推送到 Git 倉庫，Render 平台會自動檢測到變更並開始部署：

1. **登入 Render 控制台**: https://dashboard.render.com/
2. **選擇您的服務**: `rmb-sales-system-test1`
3. **監控部署狀態**: 在 "Events" 標籤中查看部署進度
4. **等待部署完成**: 通常需要 2-5 分鐘

### 3. 驗證部署成功

部署完成後，測試以下端點：

#### 基本頁面測試
- ✅ 根路徑: `https://rmb-sales-system-test1.onrender.com/`
- ✅ 登入頁面: `https://rmb-sales-system-test1.onrender.com/login`
- ✅ 數據修復頁面: `https://rmb-sales-system-test1.onrender.com/admin_data_recovery`

#### API 測試
- 🔧 數據修復 API: `POST /api/admin/data-recovery`
- 📊 數據狀態 API: `GET /api/admin/data-status`

## 🔧 修復內容總結

### 已修復的問題
1. **缺少 traceback 模組**: 添加了 `import traceback`
2. **字段名稱不匹配**: 修正了 `account.account_name` → `account.name`
3. **不存在的字段**: 修復了 `account.initial_balance` 引用
4. **增強錯誤處理**: 添加了詳細的錯誤檢查和日誌記錄
5. **導入優化**: 添加了 `timezone` 導入

### 新增功能
- 📊 數據狀態檢查 API (`/api/admin/data-status`)
- 🔍 資料庫連接檢查
- 📝 詳細的錯誤日誌記錄

## 🧪 測試驗證

### 使用測試腳本
```bash
# 測試基本連接
python test_db_connection_simple.py

# 測試數據修復 API
python test_data_recovery_fix.py
```

### 手動測試步驟
1. 訪問數據修復管理頁面
2. 點擊"刷新"按鈕檢查數據狀態
3. 點擊"執行數據修復"按鈕
4. 檢查是否成功執行並返回結果

## 📋 預期結果

### 成功情況
- ✅ 所有頁面正常訪問 (200 狀態碼)
- ✅ 數據修復 API 成功執行 (200 狀態碼)
- ✅ 返回詳細的修復結果和摘要

### 如果仍有問題
1. **檢查 Render 日誌**: 在控制台的 "Logs" 標籤中查看詳細錯誤
2. **驗證資料庫連接**: 確認 PostgreSQL 連接正常
3. **檢查模型定義**: 確認所有數據模型字段正確

## 🚨 注意事項

### 安全提醒
- 數據修復操作會直接修改資料庫
- 建議在執行前備份重要數據
- 確保只有管理員可以訪問此功能

### 性能考慮
- 數據修復操作可能耗時較長
- 建議在系統閒置時執行
- 大量數據時可能需要調整超時設置

## 📞 故障排除

### 常見問題
1. **500 錯誤持續**: 檢查 Render 日誌獲取詳細錯誤信息
2. **資料庫連接失敗**: 確認環境變數和資料庫配置
3. **模型查詢錯誤**: 檢查資料庫表結構是否與模型匹配

### 獲取幫助
- 查看 Render 平台日誌
- 檢查應用程式控制台輸出
- 使用測試腳本診斷問題

---

**部署完成後，數據修復 API 應該能夠正常工作，不再出現 500 錯誤。**
