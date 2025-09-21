#!/usr/bin/env python3
"""
本地測試腳本 - 驗證 GCS 設置
在部署到 Render 之前先在本地測試
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from google.cloud import storage
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gcs_connection():
    """測試 GCS 連線"""
    print("🔍 === 本地 GCS 連線測試 ===\n")
    
    # 1. 檢查環境變數或認證檔案
    gcs_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    gcs_bucket = os.getenv('GCS_BUCKET_NAME', 'dealsys')
    
    print(f"📁 認證檔案路徑: {gcs_credentials}")
    print(f"🪣 GCS 儲存桶: {gcs_bucket}")
    
    if not gcs_credentials:
        print("❌ 請設置 GOOGLE_APPLICATION_CREDENTIALS 環境變數")
        print("   方法 1: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json")
        print("   方法 2: 將認證檔案放在專案根目錄並命名為 gcs-key.json")
        
        # 檢查是否有本地認證檔案
        local_key = "gcs-key.json"
        if os.path.exists(local_key):
            print(f"✅ 找到本地認證檔案: {local_key}")
            gcs_credentials = local_key
        else:
            return False
    
    # 2. 檢查認證檔案是否存在
    if not os.path.exists(gcs_credentials):
        print(f"❌ 認證檔案不存在: {gcs_credentials}")
        return False
    
    print(f"✅ 認證檔案存在")
    
    # 3. 驗證 JSON 格式
    try:
        with open(gcs_credentials, 'r') as f:
            creds_data = json.load(f)
            print(f"✅ JSON 格式正確")
            print(f"   項目 ID: {creds_data.get('project_id', 'N/A')}")
            print(f"   客戶端郵箱: {creds_data.get('client_email', 'N/A')}")
    except json.JSONDecodeError:
        print("❌ 認證檔案 JSON 格式錯誤")
        return False
    except Exception as e:
        print(f"❌ 讀取認證檔案失敗: {e}")
        return False
    
    # 4. 測試 GCS 連線
    try:
        print("\n🌐 測試 GCS 連線...")
        client = storage.Client.from_service_account_json(gcs_credentials)
        
        # 測試儲存桶
        bucket = client.bucket(gcs_bucket)
        if bucket.exists():
            print(f"✅ 儲存桶 '{gcs_bucket}' 連線成功")
            
            # 列出現有檔案
            blobs = list(bucket.list_blobs(max_results=10))
            print(f"📊 儲存桶中有 {len(blobs)} 個檔案")
            
            if blobs:
                print("   最近的檔案:")
                for blob in blobs[:5]:
                    print(f"   - {blob.name} ({blob.time_created})")
        else:
            print(f"❌ 儲存桶 '{gcs_bucket}' 不存在或無權限存取")
            return False
            
    except Exception as e:
        print(f"❌ GCS 連線失敗: {e}")
        return False
    
    # 5. 測試上傳功能
    try:
        print("\n📤 測試檔案上傳...")
        
        # 創建測試檔案
        test_data = {
            '測試時間': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            '狀態': ['本地測試成功'],
            '備註': ['這是本地測試檔案']
        }
        df = pd.DataFrame(test_data)
        test_filename = f"local_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(test_filename, index=False, engine='openpyxl')
        
        # 上傳測試檔案
        blob = bucket.blob(f"test/{test_filename}")
        blob.upload_from_filename(test_filename)
        
        print(f"✅ 測試檔案上傳成功: gs://{gcs_bucket}/test/{test_filename}")
        
        # 清理本地檔案
        os.remove(test_filename)
        print(f"🧹 已清理本地測試檔案")
        
    except Exception as e:
        print(f"❌ 檔案上傳測試失敗: {e}")
        return False
    
    print("\n🎉 === 所有測試通過！GCS 設置正確 ===")
    return True

def create_render_env_template():
    """創建 Render 環境變數範本"""
    print("\n📝 === Render 環境變數設置範本 ===")
    
    gcs_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'gcs-key.json')
    
    if os.path.exists(gcs_credentials):
        with open(gcs_credentials, 'r') as f:
            creds_content = f.read()
        
        print("在 Render Dashboard 中設置以下環境變數：")
        print("\n1. GCS_CREDENTIALS_JSON (如果使用 JSON 內容方式):")
        print("   值: (將下面的 JSON 內容複製貼上)")
        print("   " + "="*50)
        print(creds_content)
        print("   " + "="*50)
        
        print("\n2. 或者使用 GOOGLE_APPLICATION_CREDENTIALS (如果上傳檔案):")
        print("   值: /tmp/gcs_key.json")
        
        print(f"\n3. GCS_BUCKET_NAME:")
        print(f"   值: dealsys")
        
        print(f"\n4. TARGET_URL:")
        print(f"   值: https://rmb-sales-system-test1.onrender.com")

def main():
    """主函數"""
    print("🚀 GCS 本地測試工具")
    print("="*50)
    
    # 檢查必要的套件
    try:
        import pandas
        import openpyxl
        from google.cloud import storage
        print("✅ 所有必要套件已安裝")
    except ImportError as e:
        print(f"❌ 缺少必要套件: {e}")
        print("請執行: pip install pandas openpyxl google-cloud-storage")
        return
    
    # 執行 GCS 測試
    if test_gcs_connection():
        create_render_env_template()
        print("\n✅ 本地測試完成！現在可以部署到 Render")
    else:
        print("\n❌ 本地測試失敗，請修正問題後重試")

if __name__ == "__main__":
    main()
