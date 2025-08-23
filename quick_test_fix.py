#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試腳本 - 驗證 SQLAlchemy 語法修復
"""

import requests
import json
from datetime import datetime

def test_data_recovery_api():
    """測試數據修復 API"""
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    recovery_url = f"{base_url}/api/admin/data-recovery"
    
    print("🔧 測試數據修復 API 修復")
    print("=" * 50)
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API 端點: {recovery_url}")
    print("-" * 50)
    
    try:
        print("📤 發送數據修復請求...")
        response = requests.post(
            recovery_url,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📥 收到響應:")
        print(f"   狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 數據修復 API 修復成功！")
            try:
                data = response.json()
                if 'status' in data and data['status'] == 'success':
                    print("✅ API 返回成功狀態")
                    
                    if 'summary' in data:
                        summary = data['summary']
                        print(f"📊 修復摘要:")
                        print(f"   庫存批次修復: {summary.get('inventory_batches_fixed', 'N/A')}")
                        print(f"   現金帳戶修復: {summary.get('cash_accounts_fixed', 'N/A')}")
                        print(f"   客戶修復: {summary.get('customers_fixed', 'N/A')}")
                    
                    if 'final_status' in data:
                        final = data['final_status']
                        print(f"📈 最終狀態:")
                        if 'inventory' in final:
                            inv = final['inventory']
                            print(f"   庫存總量: ¥{inv.get('total_original', 'N/A'):,.2f}")
                            print(f"   庫存剩餘: ¥{inv.get('total_remaining', 'N/A'):,.2f}")
                        
                        if 'cash_accounts' in final:
                            cash = final['cash_accounts']
                            print(f"   TWD 總額: NT$ {cash.get('total_twd', 'N/A'):,.2f}")
                            print(f"   RMB 總額: ¥{cash.get('total_rmb', 'N/A'):,.2f}")
                        
                        if 'receivables' in final:
                            print(f"   應收帳款: NT$ {final['receivables']:,.2f}")
                    
                    return True
                else:
                    print("⚠️  API 返回異常狀態")
                    print(f"   響應內容: {response.text[:500]}...")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  無法解析 JSON 響應: {e}")
                print(f"   響應內容: {response.text[:500]}...")
                return False
                
        elif response.status_code == 500:
            print("❌ 數據修復 API 仍然返回 500 錯誤")
            print("💡 這可能表示:")
            print("   1. 新的修復代碼還沒有部署")
            print("   2. 還有其他錯誤需要解決")
            print(f"   錯誤響應: {response.text[:500]}...")
            return False
            
        else:
            print(f"⚠️  數據修復 API 返回狀態碼: {response.status_code}")
            print(f"   響應內容: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 請求超時")
        print("💡 這可能表示系統正在部署中")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始測試 SQLAlchemy 語法修復...")
    
    success = test_data_recovery_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 恭喜！數據修復 API 已經完全修復！")
        print("✅ 您可以正常使用數據修復功能了")
        print("\n📋 下一步:")
        print("   1. 在網頁界面中點擊'執行數據修復'")
        print("   2. 檢查修復結果")
        print("   3. 驗證庫存數據一致性")
    else:
        print("⚠️  數據修復 API 仍有問題")
        print("\n📋 建議:")
        print("   1. 等待新的修復代碼部署完成")
        print("   2. 檢查 Render 控制台日誌")
        print("   3. 如果問題持續，可能需要進一步調試")
    
    print("\n🏁 測試完成")

if __name__ == "__main__":
    main()
