#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署狀態檢查腳本 - 監控 Render 平台部署進度
"""

import requests
import time
from datetime import datetime

def check_deployment_status():
    """檢查部署狀態"""
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    print("🚀 數據修復 API 修復部署狀態檢查")
    print("=" * 60)
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 部署地址: {base_url}")
    print("-" * 60)
    
    # 檢查基本頁面
    print("🔍 檢查基本頁面...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("   ✅ 根路徑正常")
        else:
            print(f"   ❌ 根路徑異常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 根路徑檢查失敗: {e}")
    
    try:
        response = requests.get(f"{base_url}/admin_data_recovery", timeout=10)
        if response.status_code == 200:
            print("   ✅ 數據修復頁面正常")
        else:
            print(f"   ❌ 數據修復頁面異常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 數據修復頁面檢查失敗: {e}")
    
    print("-" * 60)
    
    # 檢查數據修復 API
    print("🔧 檢查數據修復 API...")
    try:
        response = requests.post(
            f"{base_url}/api/admin/data-recovery",
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print("   🎉 數據修復 API 修復成功！")
            try:
                data = response.json()
                if 'status' in data and data['status'] == 'success':
                    print("   ✅ API 返回成功狀態")
                    if 'summary' in data:
                        summary = data['summary']
                        print(f"   📊 修復摘要:")
                        print(f"      庫存批次: {summary.get('inventory_batches_fixed', 'N/A')}")
                        print(f"      現金帳戶: {summary.get('cash_accounts_fixed', 'N/A')}")
                        print(f"      客戶數據: {summary.get('customers_fixed', 'N/A')}")
                else:
                    print("   ⚠️  API 返回異常狀態")
            except:
                print("   ⚠️  無法解析 API 響應")
        elif response.status_code == 500:
            print("   ❌ 數據修復 API 仍然返回 500 錯誤")
            print("   💡 這表示修復代碼可能還沒有在 Render 平台上生效")
            print("   📋 建議:")
            print("      1. 等待 Render 自動部署完成 (通常 2-5 分鐘)")
            print("      2. 檢查 Render 控制台的部署狀態")
            print("      3. 如果長時間未部署，可能需要手動觸發")
        else:
            print(f"   ⚠️  數據修復 API 返回狀態碼: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏰ 數據修復 API 請求超時")
        print("   💡 這可能表示:")
        print("      1. 系統正在部署中")
        print("      2. 資料庫連接有問題")
        print("      3. 需要等待部署完成")
    except Exception as e:
        print(f"   ❌ 數據修復 API 檢查失敗: {e}")
    
    print("-" * 60)
    
    # 檢查數據狀態 API
    print("📊 檢查數據狀態 API...")
    try:
        response = requests.get(f"{base_url}/api/admin/data-status", timeout=10)
        if response.status_code == 200:
            print("   ✅ 數據狀態 API 正常")
            try:
                data = response.json()
                if 'data' in data:
                    inventory = data['data'].get('inventory', {})
                    print(f"   📦 庫存狀態:")
                    print(f"      總批次: {inventory.get('total_batches', 'N/A')}")
                    print(f"      原始總量: ¥{inventory.get('total_original', 'N/A'):,.2f}")
                    print(f"      剩餘數量: ¥{inventory.get('total_remaining', 'N/A'):,.2f}")
                    print(f"      一致性: {'✅' if inventory.get('consistency_check') else '❌'}")
            except:
                print("   ⚠️  無法解析數據狀態響應")
        else:
            print(f"   ❌ 數據狀態 API 異常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 數據狀態 API 檢查失敗: {e}")
    
    print("-" * 60)
    
    # 部署建議
    print("📋 部署狀態分析:")
    
    if response.status_code == 200:
        print("   🎉 恭喜！數據修復 API 已經成功修復並部署")
        print("   ✅ 您可以正常使用數據修復功能了")
    else:
        print("   🔄 修復代碼可能還在部署中")
        print("   📋 下一步行動:")
        print("      1. 等待 2-5 分鐘讓 Render 完成自動部署")
        print("      2. 重新運行此腳本檢查狀態")
        print("      3. 如果問題持續，檢查 Render 控制台日誌")
    
    print("\n" + "=" * 60)
    print("🏁 檢查完成")

def main():
    """主函數"""
    check_deployment_status()
    
    # 提供重複檢查選項
    print("\n🔄 是否要重複檢查部署狀態？")
    print("   輸入 'y' 或 'yes' 開始重複檢查 (每 30 秒)")
    print("   按 Enter 退出")
    
    choice = input("您的選擇: ").strip().lower()
    
    if choice in ['y', 'yes']:
        print("\n🔄 開始重複檢查... (按 Ctrl+C 停止)")
        try:
            while True:
                time.sleep(30)
                print(f"\n🔄 重新檢查... {datetime.now().strftime('%H:%M:%S')}")
                check_deployment_status()
        except KeyboardInterrupt:
            print("\n⏹️  停止重複檢查")

if __name__ == "__main__":
    main()
