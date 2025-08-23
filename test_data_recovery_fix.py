#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復後的數據修復 API
"""

import requests
import json
from datetime import datetime

def test_data_recovery_api():
    """測試數據修復 API"""
    
    # API 端點
    base_url = "https://rmb-sales-system-test1.onrender.com"
    recovery_url = f"{base_url}/api/admin/data-recovery"
    
    print(f"🔧 測試數據修復 API: {recovery_url}")
    print(f"⏰ 測試時間: {datetime.now().isoformat()}")
    print("-" * 60)
    
    try:
        # 發送 POST 請求
        print("📤 發送數據修復請求...")
        response = requests.post(
            recovery_url,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'DataRecoveryTest/1.0'
            },
            timeout=30
        )
        
        print(f"📥 收到響應:")
        print(f"   狀態碼: {response.status_code}")
        print(f"   響應頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 數據修復成功!")
            try:
                data = response.json()
                print(f"📊 修復摘要:")
                print(f"   庫存批次修復: {data.get('summary', {}).get('inventory_batches_fixed', 'N/A')}")
                print(f"   現金帳戶修復: {data.get('summary', {}).get('cash_accounts_fixed', 'N/A')}")
                print(f"   客戶修復: {data.get('summary', {}).get('customers_fixed', 'N/A')}")
                
                if 'final_status' in data:
                    final = data['final_status']
                    print(f"📈 最終狀態:")
                    print(f"   庫存總量: ¥{final.get('inventory', {}).get('total_original', 'N/A'):,.2f}")
                    print(f"   庫存剩餘: ¥{final.get('inventory', {}).get('total_remaining', 'N/A'):,.2f}")
                    print(f"   TWD 總額: NT$ {final.get('cash_accounts', {}).get('total_twd', 'N/A'):,.2f}")
                    print(f"   RMB 總額: ¥{final.get('cash_accounts', {}).get('total_rmb', 'N/A'):,.2f}")
                    print(f"   應收帳款: NT$ {final.get('receivables', 'N/A'):,.2f}")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  響應不是有效的 JSON: {e}")
                print(f"   響應內容: {response.text[:500]}...")
                
        else:
            print(f"❌ 數據修復失敗!")
            print(f"   錯誤響應: {response.text}")
            
            # 嘗試解析錯誤信息
            try:
                error_data = response.json()
                if 'message' in error_data:
                    print(f"   錯誤信息: {error_data['message']}")
            except:
                pass
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
    
    print("-" * 60)
    print("🏁 測試完成")

if __name__ == "__main__":
    test_data_recovery_api()
