"""
線上RMB回滾機制測試指南
專門測試7773支付寶帳戶的回滾問題
"""

def print_test_guide():
    """打印測試指南"""
    print("=" * 80)
    print("線上RMB回滾機制測試指南")
    print("=" * 80)
    
    print("\n📋 測試目標：")
    print("   驗證修復後的app.py是否能正確回滾RMB帳戶餘額")
    print("   特別針對7773支付寶帳戶的問題")
    
    print("\n🔧 測試前準備：")
    print("   1. 部署修復後的app.py到線上環境")
    print("   2. 重啟服務")
    print("   3. 登入管理員帳號")
    print("   4. 備份線上資料庫（重要！）")
    
    print("\n📊 測試步驟：")
    print("   第一步：記錄初始狀態")
    print("   - 登入現金管理頁面")
    print("   - 記錄7773支付寶帳戶當前餘額（應該是4.28 RMB）")
    print("   - 記錄其他相關帳戶餘額")
    
    print("\n   第二步：創建測試買入記錄")
    print("   - 到買入頁面")
    print("   - 選擇7773的TWD帳戶作為付款帳戶")
    print("   - 選擇7773的支付寶帳戶作為收款帳戶")
    print("   - 輸入測試金額：RMB金額=100，匯率=4.0")
    print("   - 提交買入記錄")
    print("   - 記錄買入記錄ID")
    
    print("\n   第三步：驗證買入後的狀態")
    print("   - 檢查7773支付寶帳戶餘額是否增加100 RMB")
    print("   - 檢查7773的TWD帳戶餘額是否減少400 TWD")
    print("   - 檢查FIFO庫存是否新增一筆100 RMB的記錄")
    
    print("\n   第四步：執行刪除操作")
    print("   - 到買入記錄列表頁面")
    print("   - 找到剛創建的測試記錄")
    print("   - 點擊刪除/取消按鈕")
    print("   - 確認刪除操作")
    
    print("\n   第五步：驗證回滾結果")
    print("   - 檢查7773支付寶帳戶餘額是否回到初始值")
    print("   - 檢查7773的TWD帳戶餘額是否回到初始值")
    print("   - 檢查FIFO庫存記錄是否被刪除")
    
    print("\n✅ 成功標準：")
    print("   如果所有餘額都回到初始狀態，說明回滾機制修復成功")
    
    print("\n❌ 失敗情況：")
    print("   如果RMB帳戶餘額沒有回滾，說明修復不完整")
    print("   如果TWD帳戶餘額沒有回滾，說明有其他問題")
    
    print("\n🔄 如果測試失敗：")
    print("   1. 立即還原資料庫備份")
    print("   2. 檢查app.py是否正確部署")
    print("   3. 檢查日誌是否有錯誤訊息")
    print("   4. 聯繫技術支援")
    
    print("\n📝 記錄模板：")
    print("   初始狀態：")
    print("   - 7773支付寶帳戶：___ RMB")
    print("   - 7773 TWD帳戶：___ TWD")
    print("   ")
    print("   買入後：")
    print("   - 7773支付寶帳戶：___ RMB")
    print("   - 7773 TWD帳戶：___ TWD")
    print("   ")
    print("   刪除後：")
    print("   - 7773支付寶帳戶：___ RMB")
    print("   - 7773 TWD帳戶：___ TWD")
    
    print("\n🎯 關鍵檢查點：")
    print("   1. 買入記錄ID：___")
    print("   2. 刪除操作是否成功（API回應）")
    print("   3. 伺服器日誌是否顯示正確的回滾訊息")
    
    print("\n" + "=" * 80)
    print("測試完成後請回報結果")
    print("=" * 80)


def create_api_test_script():
    """創建API測試腳本"""
    print("\n📋 API測試腳本（可選）：")
    print("""
# 如果需要直接測試API，可以使用以下curl命令：

# 1. 創建買入記錄（需要先登入獲取session）
curl -X POST -H "Content-Type: application/json" \\
     -d '{
       "action": "record_purchase",
       "payment_account_id": <TWD_帳戶ID>,
       "deposit_account_id": <RMB_帳戶ID>,
       "rmb_amount": 100,
       "exchange_rate": 4.0,
       "channel_id": <渠道ID>
     }' \\
     -b "session=<登入session>" \\
     https://<你的域名>/api/buy-in

# 2. 刪除買入記錄
curl -X POST \\
     -b "session=<登入session>" \\
     https://<你的域名>/api/reverse-purchase-inventory/<買入記錄ID>
    """)


if __name__ == "__main__":
    print_test_guide()
    create_api_test_script()
