#!/usr/bin/env python3
"""
Render 健康檢查腳本
簡化版本，用於快速檢查 GCS 備份系統狀態
"""

import os
import sys
from datetime import datetime, timedelta

def main():
    print("🔍 Render GCS 備份系統健康檢查")
    print("=" * 40)
    
    # 1. 檢查環境變數
    print("\n1. 環境變數檢查:")
    creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    bucket = os.getenv('GCS_BUCKET_NAME')
    target_url = os.getenv('TARGET_URL', 'https://www.google.com')
    
    if creds:
        print(f"   ✅ GOOGLE_APPLICATION_CREDENTIALS: {creds}")
    else:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS: 未設定")
        return False
    
    if bucket:
        print(f"   ✅ GCS_BUCKET_NAME: {bucket}")
    else:
        print("   ❌ GCS_BUCKET_NAME: 未設定")
        return False
    
    print(f"   ✅ TARGET_URL: {target_url}")
    
    # 2. 檢查認證檔案
    print("\n2. 認證檔案檢查:")
    if os.path.exists(creds):
        print(f"   ✅ 認證檔案存在: {creds}")
    else:
        print(f"   ❌ 認證檔案不存在: {creds}")
        return False
    
    # 3. 測試 GCS 連線
    print("\n3. GCS 連線測試:")
    try:
        from google.cloud import storage
        client = storage.Client.from_service_account_json(creds)
        gcs_bucket = client.bucket(bucket)
        
        if gcs_bucket.exists():
            print(f"   ✅ GCS 連線成功，儲存桶 '{bucket}' 存在")
        else:
            print(f"   ❌ 儲存桶 '{bucket}' 不存在")
            return False
            
    except Exception as e:
        print(f"   ❌ GCS 連線失敗: {str(e)}")
        return False
    
    # 4. 檢查最近的備份檔案
    print("\n4. 備份檔案檢查:")
    try:
        # 檢查過去 24 小時的檔案
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        excel_files = list(gcs_bucket.list_blobs(prefix='excel/'))
        screenshot_files = list(gcs_bucket.list_blobs(prefix='screenshots/'))
        
        recent_excel = [f for f in excel_files if f.time_created.replace(tzinfo=None) > cutoff_time]
        recent_screenshots = [f for f in screenshot_files if f.time_created.replace(tzinfo=None) > cutoff_time]
        
        print(f"   📊 Excel 檔案: {len(excel_files)} 個總計, {len(recent_excel)} 個最近 24 小時")
        print(f"   📸 截圖檔案: {len(screenshot_files)} 個總計, {len(recent_screenshots)} 個最近 24 小時")
        
        if recent_excel and recent_screenshots:
            print("   ✅ 最近 24 小時內有新的備份檔案")
        else:
            print("   ⚠️ 最近 24 小時內沒有新的備份檔案")
            
    except Exception as e:
        print(f"   ❌ 檢查備份檔案失敗: {str(e)}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 健康檢查完成！系統運行正常。")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
