# 🔧 GCS 備份系統除錯指南

## 📊 **問題診斷**

根據你的 Render Dashboard，Cron Job 連續失敗，狀態碼為 1。主要問題：

### ❌ **發現的問題**
1. **認證檔案路徑錯誤** - 原本設置為範例路徑
2. **Selenium/Chrome 在容器環境的相容性問題**
3. **依賴套件版本可能不相容**

### ✅ **已修正的問題**
1. ✅ 更新了認證檔案路徑為 `/tmp/gcs_key.json`
2. ✅ 創建了簡化版測試腳本（不使用 Selenium）
3. ✅ 優化了依賴套件版本

## 🚀 **立即行動步驟**

### **第 1 步：本地測試**
```bash
# 1. 執行本地測試腳本
python test_local_gcs.py

# 2. 如果缺少套件，安裝依賴
pip install pandas openpyxl google-cloud-storage
```

### **第 2 步：準備 GCS 認證**
你需要：
1. **Google Cloud Service Account JSON 檔案**
2. **確保該帳號有 GCS 儲存桶的讀寫權限**

### **第 3 步：Render 部署選項**

#### **選項 A：使用簡化版本（推薦）**
1. 使用 `render_cron_simple.py`（已創建）
2. 更新 Render 配置為 `render_cron_simple.yaml`
3. 設置環境變數：
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcs_key.json
   GCS_BUCKET_NAME=dealsys
   ```

#### **選項 B：修復原版本**
1. 修復 Chrome/Selenium 問題
2. 添加更多容器相容性設置

### **第 4 步：Render 環境變數設置**

在 Render Dashboard 中設置：

```bash
# 必要環境變數
GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcs_key.json
GCS_BUCKET_NAME=dealsys

# 可選環境變數（用於完整版本）
TARGET_URL=https://rmb-sales-system-test1.onrender.com
```

### **第 5 步：上傳認證檔案**

**方法 1：使用 Secret Files（推薦）**
1. 在 Render Dashboard 找到 "Secret Files" 區域
2. 上傳你的 GCS JSON 認證檔案
3. 設置路徑為 `/tmp/gcs_key.json`

**方法 2：使用環境變數**
1. 添加環境變數 `GCS_CREDENTIALS_JSON`
2. 將整個 JSON 檔案內容貼上作為值

## 🧪 **測試流程**

### **本地測試**
```bash
# 設置環境變數（Windows）
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\gcs-key.json
set GCS_BUCKET_NAME=dealsys

# 設置環境變數（Linux/Mac）
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/gcs-key.json
export GCS_BUCKET_NAME=dealsys

# 執行測試
python test_local_gcs.py
```

### **Render 測試**
1. 部署簡化版本
2. 設置 Cron 為每 10 分鐘執行一次（測試用）
3. 檢查執行日誌
4. 確認 GCS 中有檔案上傳

## 📝 **配置檔案更新**

### **使用簡化版本（推薦）**
```yaml
# render_cron_simple.yaml
services:
  - type: cron
    name: dealsys-cron-test
    env: python
    buildCommand: pip install pandas openpyxl google-cloud-storage
    startCommand: python render_cron_simple.py
    schedule: "*/10 * * * *"  # 每 10 分鐘執行（測試用）
    envVars:
      - key: GOOGLE_APPLICATION_CREDENTIALS
        value: "/tmp/gcs_key.json"
      - key: GCS_BUCKET_NAME
        value: "dealsys"
```

### **恢復正常排程**
測試成功後，將排程改回：
```yaml
schedule: "0 2 * * *"  # 每天 UTC 凌晨 2 點
```

## 🔍 **除錯檢查清單**

### ✅ **環境變數檢查**
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` 路徑正確
- [ ] `GCS_BUCKET_NAME` 設置正確
- [ ] 認證檔案已上傳到 Render

### ✅ **GCS 設置檢查**
- [ ] Service Account 有儲存桶權限
- [ ] 儲存桶存在且可存取
- [ ] JSON 認證檔案格式正確

### ✅ **Render 設置檢查**
- [ ] Cron Job 服務已創建
- [ ] 依賴套件安裝成功
- [ ] 環境變數同步到 Cron 服務

## 📊 **成功指標**

### **本地測試成功**
```
✅ 認證檔案存在
✅ JSON 格式正確
✅ GCS 連線成功
✅ 檔案上傳成功
🎉 所有測試通過！
```

### **Render 部署成功**
- Cron Job 狀態為 "成功"
- 執行日誌顯示 "Cron Job 執行成功"
- GCS 儲存桶中出現新的備份檔案

## 🆘 **常見錯誤解決**

### **錯誤 1：認證檔案不存在**
```
解決方案：確保在 Render Secret Files 中上傳了認證檔案
```

### **錯誤 2：權限不足**
```
解決方案：檢查 Service Account 是否有 Storage Admin 角色
```

### **錯誤 3：儲存桶不存在**
```
解決方案：在 GCS 中創建名為 'dealsys' 的儲存桶
```

## 🎯 **下一步行動**

1. **立即執行**：`python test_local_gcs.py`
2. **如果本地測試成功**：部署簡化版本到 Render
3. **如果 Render 測試成功**：恢復正常排程
4. **如果需要完整功能**：修復原版本的 Selenium 問題

---

💡 **提示**：建議先使用簡化版本確保基本功能正常，再逐步添加複雜功能。
