#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試買入頁面下拉選單修復的腳本
"""

import urllib.request
import urllib.parse
import json
import ssl

# 忽略SSL證書驗證
ssl._create_default_https_context = ssl._create_unverified_context

def test_buy_in_dropdown():
    """測試買入頁面下拉選單功能"""
    
    base_url = "http://localhost:5000"
    
    print("=== 測試買入頁面下拉選單修復 ===")
    
    try:
        # 1. 測試獲取常用渠道列表
        print("\n1. 測試獲取常用渠道列表...")
        channels_url = f"{base_url}/api/channels/public"
        
        req = urllib.request.Request(channels_url)
        with urllib.request.urlopen(req) as response:
            channels_data = json.loads(response.read().decode('utf-8'))
            print(f"✓ 成功獲取渠道列表: {len(channels_data)} 個渠道")
            for channel in channels_data:
                print(f"  - ID: {channel['id']}, 名稱: {channel['name']}")
        
        # 2. 測試買入API（模擬從下拉選單選擇渠道）
        print("\n2. 測試買入API（下拉選單選擇渠道）...")
        
        # 模擬從下拉選單選擇第一個渠道
        if channels_data:
            selected_channel_id = channels_data[0]['id']
            print(f"選擇渠道: {channels_data[0]['name']} (ID: {selected_channel_id})")
            
            # 準備測試數據
            test_data = {
                "action": "record_purchase",
                "payment_account_id": 1,  # 假設的TWD帳戶ID
                "deposit_account_id": 2,  # 假設的RMB帳戶ID
                "rmb_amount": 1000.0,
                "exchange_rate": 4.5,
                "channel_id": str(selected_channel_id),  # 從下拉選單選擇的渠道ID
                "channel_name_manual": None
            }
            
            print(f"測試數據: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            # 發送POST請求
            buy_in_url = f"{base_url}/api/buy-in"
            data = json.dumps(test_data).encode('utf-8')
            
            req = urllib.request.Request(
                buy_in_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    print(f"✓ API響應: {response_data}")
                    
                    if response_data.get('status') == 'success':
                        print("🎉 下拉選單渠道選擇功能正常！")
                    else:
                        print(f"⚠️ API返回錯誤: {response_data.get('message')}")
                        
            except urllib.error.HTTPError as e:
                error_data = json.loads(e.read().decode('utf-8'))
                print(f"❌ HTTP錯誤 {e.code}: {error_data}")
                
        else:
            print("⚠️ 沒有可用的渠道進行測試")
        
        # 3. 測試空渠道ID的處理
        print("\n3. 測試空渠道ID的處理...")
        
        test_data_empty = {
            "action": "record_purchase",
            "payment_account_id": 1,
            "deposit_account_id": 2,
            "rmb_amount": 1000.0,
            "exchange_rate": 4.5,
            "channel_id": "",  # 空字符串
            "channel_name_manual": None
        }
        
        print(f"測試空渠道ID數據: {json.dumps(test_data_empty, ensure_ascii=False, indent=2)}")
        
        try:
            req = urllib.request.Request(
                buy_in_url,
                data=json.dumps(test_data_empty).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                print(f"✓ 空渠道ID處理響應: {response_data}")
                
        except urllib.error.HTTPError as e:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"❌ 空渠道ID處理錯誤 {e.code}: {error_data}")
        
        print("\n=== 測試完成 ===")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_buy_in_dropdown()
