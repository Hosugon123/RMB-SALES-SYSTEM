#!/usr/bin/env python3
"""
備份健康檢查腳本
檢查 GCS 中的備份狀態
"""

import os
import json
from datetime import datetime, timezone
from google.cloud import storage
from zoneinfo import ZoneInfo

def check_backup_health():
    """檢查備份健康狀態"""
    try:
        # 設置 GCS 客戶端
        client = storage.Client.from_service_account_json(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        bucket = client.bucket(os.getenv('GCS_BUCKET_NAME'))
        
        print("🔍 === 備份健康檢查 ===")
        
        # 1. 檢查健康狀態檔
        try:
            blob = bucket.blob('health/status.json')
            status_data = json.loads(blob.download_as_text())
            
            print("📊 最新備份狀態:")
            print(f"  執行時間 (UTC): {status_data.get('last_run_utc', 'N/A')}")
            print(f"  執行時間 (台北): {status_data.get('last_run_taipei', 'N/A')}")
            print(f"  上傳檔案數: {status_data.get('files_uploaded', 0)}")
            print(f"  預期檔案數: {status_data.get('expected_files', 0)}")
            print(f"  資料表備份: {status_data.get('tables_backed_up', 0)}/{status_data.get('tables_total', 0)}")
            print(f"  退出代碼: {status_data.get('exit_code', 'N/A')}")
            
            # 判斷健康狀態
            if status_data.get('exit_code') == 0:
                print("✅ 備份系統健康")
            else:
                print("❌ 備份系統異常")
                
        except Exception as e:
            print(f"❌ 無法讀取健康狀態: {e}")
        
        # 2. 檢查今天的備份檔案
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        prefix = f'database_backups/{today}/'
        
        blobs = list(bucket.list_blobs(prefix=prefix))
        print(f"\n📁 今天 ({today}) 的備份檔案:")
        
        if blobs:
            for blob in blobs:
                print(f"  ✅ {blob.name} ({blob.time_created})")
        else:
            print("  ❌ 沒有找到今天的備份檔案")
        
        # 3. 檢查最近 7 天的備份
        print(f"\n📅 最近 7 天的備份:")
        for i in range(7):
            check_date = datetime.now(timezone.utc).strftime('%Y%m%d')
            prefix = f'database_backups/{check_date}/'
            day_blobs = list(bucket.list_blobs(prefix=prefix))
            
            if day_blobs:
                latest = max(day_blobs, key=lambda x: x.time_created)
                print(f"  {check_date}: ✅ {len(day_blobs)} 個檔案 (最新: {latest.time_created})")
            else:
                print(f"  {check_date}: ❌ 無備份")
            
            # 計算前一天
            from datetime import timedelta
            check_date = (datetime.now(timezone.utc) - timedelta(days=i+1)).strftime('%Y%m%d')
        
        print("\n🎯 檢查完成")
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    check_backup_health()

