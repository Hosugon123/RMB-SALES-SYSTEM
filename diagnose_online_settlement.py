#!/usr/bin/env python3
"""
線上環境銷帳問題診斷腳本
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_settlement_api():
    """測試銷帳API"""
    print("🔍 測試線上銷帳API...")
    
    # 線上環境URL
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    # 測試數據
    test_data = {
        "customer_id": 1,
        "amount": 1.0,
        "account_id": 25,
        "note": "API測試"
    }
    
    try:
        # 發送POST請求
        response = requests.post(
            f"{base_url}/api/settlement",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 HTTP狀態碼: {response.status_code}")
        print(f"📡 回應標頭: {dict(response.headers)}")
        
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

def check_online_health():
    """檢查線上環境健康狀態"""
    print("🔍 檢查線上環境健康狀態...")
    
    base_url = "https://rmb-sales-system-test1.onrender.com"
    
    try:
        # 檢查根路徑
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"📡 根路徑狀態: {response.status_code}")
        
        # 檢查健康檢查端點（如果存在）
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            print(f"📡 健康檢查狀態: {health_response.status_code}")
            if health_response.status_code == 200:
                print(f"📡 健康檢查回應: {health_response.text}")
        except:
            print("📡 健康檢查端點不存在")
        
        # 檢查登入頁面
        login_response = requests.get(f"{base_url}/login", timeout=10)
        print(f"📡 登入頁面狀態: {login_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

def analyze_error_patterns():
    """分析錯誤模式"""
    print("🔍 分析錯誤模式...")
    
    # 常見的500錯誤原因
    common_causes = [
        "資料庫連接失敗",
        "表格結構不匹配",
        "欄位類型錯誤",
        "外鍵約束問題",
        "權限不足",
        "環境變數缺失",
        "依賴套件問題",
        "記憶體不足",
        "超時問題"
    ]
    
    print("📋 常見的500錯誤原因:")
    for i, cause in enumerate(common_causes, 1):
        print(f"   {i}. {cause}")
    
    print("\n🔧 建議的排查步驟:")
    print("   1. 檢查Render服務日誌")
    print("   2. 檢查資料庫連接狀態")
    print("   3. 檢查環境變數設置")
    print("   4. 檢查依賴套件版本")
    print("   5. 檢查資料庫表格結構")
    
    return True

def create_debug_endpoint():
    """創建調試端點建議"""
    print("🔧 創建調試端點建議...")
    
    debug_code = '''
@app.route("/debug/settlement", methods=["GET"])
def debug_settlement():
    """銷帳調試端點"""
    try:
        # 檢查資料庫連接
        db_status = "正常" if db.session.execute(text("SELECT 1")).scalar() else "異常"
        
        # 檢查表格結構
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('customers', 'cash_accounts', 'ledger_entries', 'cash_logs', 'user')
        """)
        tables = [row[0] for row in db.session.execute(tables_query).fetchall()]
        
        # 檢查用戶數據
        user_count = db.session.execute(text("SELECT COUNT(*) FROM \"user\"")).scalar()
        
        # 檢查客戶數據
        customer_count = db.session.execute(text("SELECT COUNT(*) FROM customers WHERE total_receivables_twd > 0")).scalar()
        
        # 檢查帳戶數據
        account_count = db.session.execute(text("SELECT COUNT(*) FROM cash_accounts WHERE currency = 'TWD' AND is_active = true")).scalar()
        
        return jsonify({
            "status": "success",
            "database_status": db_status,
            "tables": tables,
            "user_count": user_count,
            "customer_count": customer_count,
            "account_count": account_count,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    '''
    
    print("📝 建議在app.py中添加以下調試端點:")
    print(debug_code)
    
    return True

def main():
    """主函數"""
    print("線上環境銷帳問題診斷")
    print("=" * 50)
    
    # 1. 檢查線上環境健康狀態
    if not check_online_health():
        print("❌ 線上環境健康檢查失敗")
        return False
    
    # 2. 測試銷帳API
    if not test_settlement_api():
        print("❌ 銷帳API測試失敗")
    
    # 3. 分析錯誤模式
    analyze_error_patterns()
    
    # 4. 創建調試端點建議
    create_debug_endpoint()
    
    print("\n📋 下一步建議:")
    print("1. 在Render Dashboard中查看服務日誌")
    print("2. 添加調試端點到app.py")
    print("3. 檢查PostgreSQL資料庫結構")
    print("4. 確認環境變數設置")
    
    return True

if __name__ == "__main__":
    main()
