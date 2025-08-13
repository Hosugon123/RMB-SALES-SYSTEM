#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試渠道管理功能的腳本
"""

import requests
import json

# 測試配置
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
CHANNELS_PUBLIC_URL = f"{BASE_URL}/api/channels/public"
CHANNEL_MANAGE_URL = f"{BASE_URL}/api/channel"

def test_channel_features():
    """測試渠道管理功能"""
    print("=== 測試渠道管理功能 ===")
    
    # 創建會話來保持登入狀態
    session = requests.Session()
    
    try:
        # 1. 測試登入
        print("\n1. 測試登入...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = session.post(LOGIN_URL, data=login_data)
        if login_response.status_code == 200:
            print("✓ 登入成功")
        else:
            print(f"✗ 登入失敗: {login_response.status_code}")
            return
        
        # 2. 測試獲取公開渠道列表
        print("\n2. 測試獲取公開渠道列表...")
        channels_response = session.get(CHANNELS_PUBLIC_URL)
        if channels_response.status_code == 200:
            channels = channels_response.json()
            print(f"✓ 成功獲取渠道列表: {len(channels)} 個渠道")
            for channel in channels:
                print(f"  - {channel['name']} (ID: {channel['id']})")
        else:
            print(f"✗ 獲取渠道列表失敗: {channels_response.status_code}")
            print(f"  回應內容: {channels_response.text}")
        
        # 3. 測試新增渠道
        print("\n3. 測試新增渠道...")
        new_channel_data = {
            "name": "測試渠道_" + str(hash(str(channels_response.elapsed))[-4:]
        }
        
        add_response = session.post(
            CHANNEL_MANAGE_URL, 
            json=new_channel_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if add_response.status_code == 200:
            result = add_response.json()
            print(f"✓ 成功新增渠道: {result['message']}")
            new_channel_id = result['channel']['id']
            
            # 4. 測試刪除渠道
            print("\n4. 測試刪除渠道...")
            delete_data = {"id": new_channel_id}
            delete_response = session.post(
                CHANNEL_MANAGE_URL,
                json=delete_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if delete_response.status_code == 200:
                print("✓ 成功刪除測試渠道")
            else:
                print(f"✗ 刪除渠道失敗: {delete_response.status_code}")
                print(f"  回應內容: {delete_response.text}")
        else:
            print(f"✗ 新增渠道失敗: {add_response.status_code}")
            print(f"  回應內容: {add_response.text}")
        
        print("\n=== 測試完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("✗ 無法連接到Flask應用程序，請確保應用正在運行")
    except Exception as e:
        print(f"✗ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_channel_features()
