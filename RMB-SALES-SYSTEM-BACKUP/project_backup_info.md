# RMB 銷售系統專案備份信息

## 備份時間
2025年8月30日

## 專案概述
這是一個完整的 RMB 銷售管理系統，包含以下主要功能：
- 現金管理
- 庫存管理
- 銷售記錄
- 用戶管理
- 應收賬款管理
- FIFO 庫存追蹤
- 匯率管理

## 主要文件結構
```
RMB-SALES-SYSTEM/
├── app.py (主應用程序 - 265KB)
├── models.py (數據模型)
├── requirements.txt (Python 依賴)
├── static/ (靜態文件)
├── templates/ (HTML 模板)
├── migrations/ (數據庫遷移)
└── instance/ (實例配置)
```

## 技術棧
- 後端：Flask (Python)
- 數據庫：SQLite (通過 Alembic 管理)
- 前端：HTML + JavaScript
- 樣式：Bootstrap

## 重要配置
- 數據庫：SQLite 文件存儲在 instance/ 目錄
- 環境變量：.flaskenv 文件
- 備份配置：backup_config.json

## 恢復步驟
1. 確保 Python 環境已安裝
2. 安裝依賴：`pip install -r requirements.txt`
3. 運行數據庫遷移：`flask db upgrade`
4. 啟動應用：`flask run`

## 注意事項
- 專案包含多個 .DANGER 擴展名的數據清空腳本
- 數據庫可能會被自動清空，需要進一步調查原因
- 建議在恢復前檢查是否有定時任務或自動觸發機制

## 當前狀態
專案已完整備份，可以安全地進行新專案開發。

