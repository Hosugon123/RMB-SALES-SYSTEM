# Render Cron Job - Excel 生成與網頁截圖上傳

這個專案包含一個 Python 腳本，用於在 Render 服務上執行定時任務，生成 Excel 檔案、截取網頁截圖並上傳到 Google Cloud Storage。

## 功能特色

- 📊 生成範例 Excel 檔案（使用 pandas）
- 📸 使用 Headless Chrome 截取網頁截圖
- ☁️ 自動上傳檔案到 Google Cloud Storage
- 🧹 自動清理本地臨時檔案
- 📝 完整的日誌記錄
- ⚙️ 支援 Render 容器環境

## 環境變數設定

在 Render 服務中設定以下環境變數：

```bash
# Google Cloud Storage 認證
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# GCS 儲存桶名稱
GCS_BUCKET_NAME=your-bucket-name

# 截圖目標網址（可選，預設為 Google）
TARGET_URL=https://your-target-website.com
```

## 安裝與使用

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定 Google Cloud Storage

1. 在 Google Cloud Console 創建服務帳戶
2. 下載服務帳戶密鑰 JSON 檔案
3. 將檔案上傳到 Render 服務
4. 設定 `GOOGLE_APPLICATION_CREDENTIALS` 環境變數

### 3. 執行腳本

```bash
python render_cron_job.py
```

## Render Cron Job 設定

在 Render 中設定 Cron Job：

1. 進入 Render Dashboard
2. 選擇 "Cron Jobs"
3. 創建新的 Cron Job
4. 設定執行時間（例如：每小時執行一次）
5. 上傳程式碼並設定環境變數

### Cron Job 設定範例

```bash
# 每小時執行一次
0 * * * *

# 每天凌晨 2 點執行
0 2 * * *

# 每週一凌晨 3 點執行
0 3 * * 1
```

## 檔案結構

```
├── render_cron_job.py    # 主要腳本
├── requirements.txt      # Python 依賴套件
└── README.md            # 說明文件
```

## 輸出檔案

腳本會生成以下檔案：

- `sample_data_YYYYMMDD_HHMMSS.xlsx` - 範例 Excel 檔案
- `screenshot_YYYYMMDD_HHMMSS.png` - 網頁截圖
- `cron_job.log` - 執行日誌

## 日誌記錄

腳本會記錄以下資訊：

- 執行開始和結束時間
- 每個步驟的進度
- 錯誤訊息和例外處理
- 檔案上傳狀態

## 錯誤處理

腳本包含完整的錯誤處理機制：

- Chrome 驅動程式設置失敗
- 網頁載入超時
- GCS 上傳失敗
- 檔案清理錯誤

## 自訂設定

您可以修改以下部分來自訂腳本：

1. **Excel 資料結構** - 修改 `generate_excel_file()` 方法
2. **截圖設定** - 調整 Chrome 選項
3. **檔案命名** - 修改時間戳格式
4. **GCS 路徑** - 自訂上傳路徑結構

## 故障排除

### 常見問題

1. **Chrome 驅動程式問題**
   - 確保使用最新版本的 webdriver-manager
   - 檢查 Chrome 選項設定

2. **GCS 認證問題**
   - 確認服務帳戶密鑰檔案路徑正確
   - 檢查 GCS 儲存桶權限設定

3. **記憶體不足**
   - 調整 Chrome 選項減少記憶體使用
   - 考慮使用更小的視窗大小

### 日誌檢查

查看 `cron_job.log` 檔案以獲取詳細的執行資訊和錯誤訊息。

## 授權

此專案使用 MIT 授權條款。