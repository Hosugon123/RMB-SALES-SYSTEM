#!/usr/bin/env python3
"""
優化部署測試腳本
驗證PostgreSQL欄位修復和API優化效果
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_postgresql_columns_fix():
    """測試PostgreSQL欄位修復"""
    print("🧪 測試PostgreSQL欄位修復...")
    
    try:
        # 導入修復腳本
        import fix_postgresql_columns
        
        # 測試修復函數
        result = fix_postgresql_columns.fix_ledger_entries_columns()
        
        if result:
            print("✅ PostgreSQL欄位修復測試通過")
            return True
        else:
            print("❌ PostgreSQL欄位修復測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ PostgreSQL欄位修復測試異常: {e}")
        return False

def test_settlement_api_optimized():
    """測試優化後的銷帳API"""
    print("\n🧪 測試優化後的銷帳API...")
    
    # 線上環境URL
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 測試數據
    test_data = {
        "customer_id": 1,
        "amount": 0.01,  # 使用很小的金額進行測試
        "account_id": 25,
        "note": "優化部署測試"
    }
    
    try:
        print(f"📡 發送測試請求到: {base_url}/api/settlement")
        print(f"📡 測試數據: {test_data}")
        
        # 發送POST請求
        response = requests.post(
            f"{base_url}/api/settlement",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 HTTP狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功回應: {result}")
            return True
        else:
            print(f"❌ 錯誤回應: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_application_startup():
    """測試應用程式啟動"""
    print("\n🧪 測試應用程式啟動...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 檢查根路徑
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"📡 應用程式狀態: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 應用程式正常啟動")
            return True
        else:
            print("❌ 應用程式啟動異常")
            return False
            
    except Exception as e:
        print(f"❌ 應用程式啟動測試失敗: {e}")
        return False

def test_api_performance():
    """測試API性能"""
    print("\n🧪 測試API性能...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    test_data = {
        "customer_id": 1,
        "amount": 0.01,
        "account_id": 25,
        "note": "性能測試"
    }
    
    try:
        # 測試多次請求的響應時間
        response_times = []
        
        for i in range(3):
            start_time = datetime.now()
            
            response = requests.post(
                f"{base_url}/api/settlement",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            response_times.append(response_time)
            
            print(f"📡 請求 {i+1}: {response.status_code} ({response_time:.2f}s)")
        
        avg_response_time = sum(response_times) / len(response_times)
        print(f"📊 平均響應時間: {avg_response_time:.2f}s")
        
        if avg_response_time < 5.0:  # 5秒內響應認為是好的
            print("✅ API性能測試通過")
            return True
        else:
            print("⚠️ API響應時間較長")
            return False
            
    except Exception as e:
        print(f"❌ API性能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("優化部署測試")
    print("=" * 50)
    
    tests = [
        ("PostgreSQL欄位修復", test_postgresql_columns_fix),
        ("應用程式啟動", test_application_startup),
        ("銷帳API功能", test_settlement_api_optimized),
        ("API性能", test_api_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"[SUCCESS] {test_name} 測試通過")
            else:
                print(f"[FAILED] {test_name} 測試失敗")
        except Exception as e:
            print(f"[ERROR] {test_name} 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("\n🎉 優化部署測試全部通過！")
        print("✅ PostgreSQL欄位修復正常")
        print("✅ 應用程式啟動正常")
        print("✅ 銷帳API功能正常")
        print("✅ API性能良好")
        print("\n🚀 系統已優化完成，可以正常使用！")
        return True
    else:
        print(f"\n⚠️ 部分測試失敗 ({total-passed}/{total})")
        print("建議檢查部署日誌和配置")
        return False

if __name__ == "__main__":
    main()
