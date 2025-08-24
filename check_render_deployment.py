#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render 部署狀態檢查腳本
檢查數字輸入修復是否已正確部署
"""

import requests
import json
import time
from datetime import datetime

def check_render_deployment():
    """檢查 Render 部署狀態"""
    
    # 請將此 URL 替換為您的實際 Render 應用程式 URL
    base_url = "https://your-app-name.onrender.com"  # 請修改為您的實際 URL
    
    print("🔍 開始檢查 Render 部署狀態...")
    print(f"📍 目標 URL: {base_url}")
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # 檢查基本連接
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✅ 基本連接: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 基本連接失敗: {e}")
        return False
    
    # 檢查關鍵頁面
    test_pages = [
        "/sales_entry",
        "/buy_in", 
        "/card_purchase",
        "/exchange_rate",
        "/inventory_management"
    ]
    
    print("\n📄 檢查關鍵頁面...")
    for page in test_pages:
        try:
            url = f"{base_url}{page}"
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {page}: HTTP {response.status_code}")
            
            # 檢查頁面內容是否包含修復後的程式碼
            if response.status_code == 200:
                content = response.text
                if 'type="text"' in content and 'pattern="[0-9]*\.?[0-9]*"' in content:
                    print(f"   ✅ 數字輸入修復已部署")
                else:
                    print(f"   ❌ 數字輸入修復未部署")
                    
        except Exception as e:
            print(f"❌ {page}: {e}")
    
    # 檢查 JavaScript 檔案
    print("\n🔧 檢查 JavaScript 檔案...")
    js_files = [
        "/static/js/enhanced_number_input.js"
    ]
    
    for js_file in js_files:
        try:
            url = f"{base_url}{js_file}"
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {js_file}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                if 'EnhancedNumberInput' in content and 'setupNumberInputFormatting' in content:
                    print(f"   ✅ 增強數字輸入腳本已部署")
                else:
                    print(f"   ❌ 增強數字輸入腳本未部署")
                    
        except Exception as e:
            print(f"❌ {js_file}: {e}")
    
    # 檢查 base.html 模板
    print("\n📋 檢查基礎模板...")
    try:
        # 通過訪問任何頁面來檢查 base.html 的內容
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 200:
            content = response.text
            if 'enhanced_number_input.js' in content:
                print("✅ 基礎模板已包含增強數字輸入腳本")
            else:
                print("❌ 基礎模板未包含增強數字輸入腳本")
        else:
            print(f"❌ 無法檢查基礎模板: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 檢查基礎模板失敗: {e}")
    
    print("\n" + "=" * 60)
    print("📊 部署狀態檢查完成")
    print("💡 如果發現問題，請：")
    print("   1. 在 Render Dashboard 中手動觸發重新部署")
    print("   2. 檢查部署日誌是否有錯誤")
    print("   3. 等待幾分鐘讓 CDN 快取更新")
    print("   4. 清除瀏覽器快取後重新測試")

def test_number_input_functionality():
    """測試數字輸入功能"""
    print("\n🧪 測試數字輸入功能...")
    
    # 這裡可以添加實際的功能測試
    # 由於這是本地腳本，我們只能提供測試建議
    
    print("💡 請在瀏覽器中測試以下功能：")
    print("   1. 訪問銷售頁面 (/sales_entry)")
    print("   2. 在金額欄位輸入 1,000")
    print("   3. 檢查是否出現錯誤訊息")
    print("   4. 如果沒有錯誤，表示修復已生效")

if __name__ == "__main__":
    print("🚀 Render 部署狀態檢查工具")
    print("請先修改腳本中的 base_url 為您的實際 Render 應用程式 URL")
    print()
    
    # 檢查部署狀態
    check_render_deployment()
    
    # 提供測試建議
    test_number_input_functionality()
