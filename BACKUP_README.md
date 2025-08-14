# 🔄 資料庫備份系統使用說明

## 📋 系統概述

這是一個完整的資料庫備份管理系統，專為 RMB 銷售管理系統設計，支援：
- 自動定期備份
- 本地備份管理
- 雲端同步備份
- 備份壓縮和清理
- 一鍵恢復功能

## 🚀 快速開始

### 1. 手動創建備份
```bash
# 創建備份
python backup_manager.py create

# 創建指定名稱的備份
python backup_manager.py create --name "重要資料備份"

# 查看備份狀態
python backup_manager.py status

# 列出所有備份
python backup_manager.py list
```

### 2. 從備份恢復
```bash
# 恢復指定備份
python backup_manager.py restore --name "backup_20250814_120000"

# 注意：恢復前會自動創建安全備份
```

### 3. 配置備份設定
```bash
# 設定最大備份數量
python backup_manager.py config --max-backups 20

# 設定備份間隔（小時）
python backup_manager.py config --interval 12

# 啟用雲端同步
python backup_manager.py config --cloud-sync --cloud-path "/path/to/cloud/drive"
```

## ⚙️ 配置選項

### 基本配置
- `max_backups`: 保留的最大備份數量（預設：10）
- `backup_interval_hours`: 備份間隔（小時，預設：24）
- `compress_backups`: 是否壓縮備份（預設：true）

### 雲端同步配置
- `cloud_sync`: 是否啟用雲端同步（預設：false）
- `cloud_drive_path`: 雲端硬碟路徑

## 📁 備份存儲位置

### 本地備份
- **目錄**: `./backups/`
- **格式**: `backup_YYYYMMDD_HHMMSS.zip`
- **內容**: 
  - 資料庫檔案 (`sales_system_v4.db`)
  - 配置檔案
  - 備份資訊 (`backup_info.json`)

### 備份檔案結構
```
backups/
├── backup_20250814_120000.zip
├── backup_20250813_120000.zip
└── backup_20250812_120000.zip
```

## 🔄 自動備份

### 在 Render 上設置自動備份

1. **創建 Cron Job**（如果支援）
   ```bash
   # 每小時執行一次備份檢查
   0 * * * * cd /opt/render/project/src && python auto_backup.py
   ```

2. **使用 Render 的 Cron Jobs 服務**
   - 創建新的 Cron Job 服務
   - 設定執行命令：`python auto_backup.py`
   - 設定執行頻率：每小時或每天

3. **手動定期執行**
   ```bash
   # 在 Render 控制台執行
   cd /opt/render/project/src
   python auto_backup.py
   ```

## 🛡️ 安全措施

### 恢復前安全備份
- 恢復備份前會自動創建當前資料庫的安全備份
- 安全備份命名格式：`sales_system_v4_safety_YYYYMMDD_HHMMSS.db`

### 備份驗證
- 每個備份都包含詳細的備份資訊
- 支援備份完整性檢查
- 自動清理過期備份

## 📊 監控和日誌

### 日誌檔案
- **備份日誌**: `backup.log`
- **自動清理**: 超過 30 天的日誌會自動刪除

### 備份狀態檢查
```bash
# 檢查備份狀態
python backup_manager.py status

# 輸出範例：
# 📊 備份狀態:
#   總備份數量: 5
#   備份目錄: /opt/render/project/src/backups
#   最新備份: backup_20250814_120000.zip
#   備份時間: 2025-08-14 12:00:00
#   下次備份: 2025-08-15 12:00:00
```

## 🔧 故障排除

### 常見問題

1. **備份創建失敗**
   - 檢查磁碟空間
   - 確認資料庫檔案存在
   - 查看錯誤日誌

2. **恢復失敗**
   - 確認備份檔案完整
   - 檢查檔案權限
   - 驗證備份格式

3. **雲端同步失敗**
   - 確認雲端路徑正確
   - 檢查網路連接
   - 驗證同步權限

### 調試模式
```bash
# 啟用詳細日誌
export PYTHONPATH=.
python -u backup_manager.py create --verbose
```

## 📈 最佳實踐

### 備份策略
- **頻率**: 建議每 12-24 小時備份一次
- **保留**: 保留最近 10-20 個備份
- **測試**: 定期測試備份恢復功能

### 雲端同步建議
- 使用 Google Drive 或 Dropbox
- 設定自動同步
- 定期檢查同步狀態

### 監控建議
- 設置備份失敗通知
- 監控磁碟空間使用
- 定期檢查備份完整性

## 🆘 緊急恢復

### 快速恢復步驟
1. 停止應用程式
2. 執行恢復命令
3. 驗證資料完整性
4. 重啟應用程式

```bash
# 緊急恢復範例
python backup_manager.py restore --name "backup_20250814_120000"
```

## 📞 技術支援

如果遇到問題，請：
1. 檢查 `backup.log` 日誌檔案
2. 執行 `python backup_manager.py status` 檢查狀態
3. 查看錯誤訊息和堆疊追蹤
4. 聯繫技術支援團隊

---

**版本**: 1.0.0  
**更新日期**: 2025-08-14  
**維護者**: RMB 銷售管理系統團隊
