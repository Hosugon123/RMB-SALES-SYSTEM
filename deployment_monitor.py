#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署監控腳本 - 監控 Render 平台部署進度並提供手動觸發選項
"""

import requests
import time
import json
from datetime import datetime, timedelta

class DeploymentMonitor:
    def __init__(self):
        self.base_url = "https://rmb-sales-system-test1.onrender.com"
        self.deployment_start_time = None
        self.last_check_time = None
        
    def check_basic_pages(self):
        """檢查基本頁面"""
        print("🔍 檢查基本頁面...")
        
        pages = [
            ("/", "根路徑"),
            ("/admin_data_recovery", "數據修復頁面"),
            ("/login", "登入頁面")
        ]
        
        all_ok = True
        for path, name in pages:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {name}正常")
                else:
                    print(f"   ❌ {name}異常: {response.status_code}")
                    all_ok = False
            except Exception as e:
                print(f"   ❌ {name}檢查失敗: {e}")
                all_ok = False
        
        return all_ok
    
    def check_data_recovery_api(self):
        """檢查數據修復 API"""
        print("\n🔧 檢查數據修復 API...")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/data-recovery",
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
                        
                        if 'final_status' in data:
                            final = data['final_status']
                            print(f"   📈 最終狀態:")
                            if 'inventory' in final:
                                inv = final['inventory']
                                print(f"      庫存總量: ¥{inv.get('total_original', 'N/A'):,.2f}")
                                print(f"      庫存剩餘: ¥{inv.get('total_remaining', 'N/A'):,.2f}")
                            
                            if 'cash_accounts' in final:
                                cash = final['cash_accounts']
                                print(f"      TWD 總額: NT$ {cash.get('total_twd', 'N/A'):,.2f}")
                                print(f"      RMB 總額: ¥{cash.get('total_rmb', 'N/A'):,.2f}")
                            
                            if 'receivables' in final:
                                print(f"      應收帳款: NT$ {final['receivables']:,.2f}")
                        
                        return True
                    else:
                        print("   ⚠️  API 返回異常狀態")
                        return False
                except Exception as e:
                    print(f"   ⚠️  無法解析 API 響應: {e}")
                    return False
            elif response.status_code == 500:
                print("   ❌ 數據修復 API 仍然返回 500 錯誤")
                print("   💡 這表示修復代碼可能還沒有在 Render 平台上生效")
                return False
            else:
                print(f"   ⚠️  數據修復 API 返回狀態碼: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ⏰ 數據修復 API 請求超時")
            print("   💡 這可能表示系統正在部署中")
            return False
        except Exception as e:
            print(f"   ❌ 數據修復 API 檢查失敗: {e}")
            return False
    
    def check_data_status_api(self):
        """檢查數據狀態 API"""
        print("\n📊 檢查數據狀態 API...")
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/data-status", timeout=10)
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
                        
                        cash_accounts = data['data'].get('cash_accounts', {})
                        print(f"   💰 現金帳戶:")
                        print(f"      TWD 帳戶: {cash_accounts.get('twd_accounts', 'N/A')}")
                        print(f"      RMB 帳戶: {cash_accounts.get('rmb_accounts', 'N/A')}")
                        print(f"      總 TWD: NT$ {cash_accounts.get('total_twd', 'N/A'):,.2f}")
                        print(f"      總 RMB: ¥{cash_accounts.get('total_rmb', 'N/A'):,.2f}")
                        
                        customers = data['data'].get('customers', {})
                        print(f"   👥 客戶狀態:")
                        print(f"      總客戶: {customers.get('total_customers', 'N/A')}")
                        print(f"      應收帳款: NT$ {customers.get('total_receivables', 'N/A'):,.2f}")
                        
                        return True
                except Exception as e:
                    print(f"   ⚠️  無法解析數據狀態響應: {e}")
                    return False
            else:
                print(f"   ❌ 數據狀態 API 異常: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 數據狀態 API 檢查失敗: {e}")
            return False
    
    def estimate_deployment_time(self):
        """估算部署時間"""
        if self.deployment_start_time:
            elapsed = datetime.now() - self.deployment_start_time
            print(f"\n⏱️  部署已進行: {elapsed}")
            
            if elapsed < timedelta(minutes=2):
                print("   💡 部署通常需要 2-5 分鐘，請耐心等待")
            elif elapsed < timedelta(minutes=5):
                print("   💡 部署應該快完成了，請稍等")
            else:
                print("   ⚠️  部署時間超過預期，可能需要檢查 Render 控制台")
    
    def provide_deployment_advice(self):
        """提供部署建議"""
        print("\n📋 部署狀態分析:")
        
        if self.deployment_start_time:
            elapsed = datetime.now() - self.deployment_start_time
            if elapsed < timedelta(minutes=5):
                print("   🔄 修復代碼正在部署中...")
                print("   📋 建議:")
                print("      1. 繼續等待 Render 完成自動部署")
                print("      2. 每 30 秒重新檢查一次")
                print("      3. 如果 5 分鐘後仍未部署，檢查 Render 控制台")
            else:
                print("   ⚠️  部署時間超過預期")
                print("   📋 建議:")
                print("      1. 檢查 Render 控制台的部署狀態")
                print("      2. 查看是否有部署錯誤")
                print("      3. 考慮手動觸發重新部署")
        else:
            print("   🔄 修復代碼可能還在部署中")
            print("   📋 建議:")
            print("      1. 等待 2-5 分鐘讓 Render 完成自動部署")
            print("      2. 重新運行此腳本檢查狀態")
            print("      3. 如果問題持續，檢查 Render 控制台日誌")
    
    def manual_deployment_trigger(self):
        """手動觸發部署的說明"""
        print("\n🔧 手動觸發部署選項:")
        print("   如果自動部署遲遲不開始，您可以:")
        print("   1. 登入 Render 控制台: https://dashboard.render.com/")
        print("   2. 選擇您的服務: rmb-sales-system-test1")
        print("   3. 在 'Manual Deploy' 部分點擊 'Deploy latest commit'")
        print("   4. 等待部署完成")
        print("   5. 重新運行此腳本檢查狀態")
    
    def run_full_check(self):
        """執行完整檢查"""
        print("🚀 數據修復 API 修復部署狀態檢查")
        print("=" * 60)
        print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 部署地址: {self.base_url}")
        print("-" * 60)
        
        # 記錄檢查時間
        self.last_check_time = datetime.now()
        
        # 執行檢查
        pages_ok = self.check_basic_pages()
        recovery_api_ok = self.check_data_recovery_api()
        status_api_ok = self.check_data_status_api()
        
        # 估算部署時間
        self.estimate_deployment_time()
        
        # 提供建議
        self.provide_deployment_advice()
        
        # 如果數據修復 API 仍然失敗，提供手動觸發選項
        if not recovery_api_ok:
            self.manual_deployment_trigger()
        
        print("\n" + "=" * 60)
        print("🏁 檢查完成")
        
        return recovery_api_ok
    
    def start_monitoring(self):
        """開始監控部署"""
        print("🔄 開始部署監控...")
        print("   按 Ctrl+C 停止監控")
        
        try:
            while True:
                print(f"\n🔄 重新檢查... {datetime.now().strftime('%H:%M:%S')}")
                success = self.run_full_check()
                
                if success:
                    print("\n🎉 恭喜！數據修復 API 已經成功修復並部署！")
                    print("✅ 您可以正常使用數據修復功能了")
                    break
                
                print(f"\n⏳ 等待 30 秒後重新檢查...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n⏹️  停止部署監控")

def main():
    """主函數"""
    monitor = DeploymentMonitor()
    
    # 執行一次檢查
    success = monitor.run_full_check()
    
    if success:
        print("\n🎉 數據修復 API 已經成功修復並部署！")
        return
    
    # 提供監控選項
    print("\n🔄 部署監控選項:")
    print("   1. 開始自動監控 (每 30 秒檢查一次)")
    print("   2. 手動重新檢查")
    print("   3. 退出")
    
    while True:
        choice = input("\n請選擇 (1-3): ").strip()
        
        if choice == "1":
            monitor.deployment_start_time = datetime.now()
            monitor.start_monitoring()
            break
        elif choice == "2":
            monitor.run_full_check()
        elif choice == "3":
            print("👋 退出部署監控")
            break
        else:
            print("❌ 無效選擇，請輸入 1-3")

if __name__ == "__main__":
    main()
