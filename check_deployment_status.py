#!/usr/bin/env python3
"""
檢查部署狀態
"""

import requests
import json

def check_deployment_status():
    """檢查部署狀態"""
    print("檢查線上環境部署狀態...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 檢查主頁面
        print("1. 檢查主頁面...")
        response = requests.get(base_url, timeout=10)
        print(f"   狀態碼: {response.status_code}")
        
        # 檢查現金管理頁面
        print("2. 檢查現金管理頁面...")
        response = requests.get(f"{base_url}/admin/cash_management", timeout=10)
        print(f"   狀態碼: {response.status_code}")
        
        # 檢查API端點
        print("3. 檢查API端點...")
        try:
            response = requests.get(f"{base_url}/api/cash_management/transactions?page=1", timeout=10)
            print(f"   狀態碼: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   響應格式: JSON (包含 {len(data.get('transactions', []))} 筆記錄)")
                except:
                    print(f"   響應格式: 非JSON")
                    print(f"   響應內容: {response.text[:200]}...")
            else:
                print(f"   錯誤響應: {response.text[:200]}...")
        except Exception as e:
            print(f"   API請求失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"檢查失敗: {e}")
        return False

def main():
    """主函數"""
    print("檢查線上環境部署狀態")
    print("=" * 50)
    
    if check_deployment_status():
        print("\n檢查完成")
    else:
        print("\n檢查失敗")

if __name__ == "__main__":
    main()
