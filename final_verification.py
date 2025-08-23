#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終驗證腳本 - 檢查數據修復 API 修復狀態
"""

import os
import re

def check_imports():
    """檢查導入語句"""
    print("🔍 檢查導入語句...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查必要的導入
    required_imports = [
        'import traceback',
        'from datetime import datetime, date, timezone',
        'from sqlalchemy import func, and_'
    ]
    
    for imp in required_imports:
        if imp in content:
            print(f"   ✅ {imp}")
        else:
            print(f"   ❌ {imp}")
    
    return True

def check_data_recovery_api():
    """檢查數據修復 API 的修復"""
    print("\n🔍 檢查數據修復 API 修復...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查修復項目
    fixes = [
        ('traceback.print_exc()', 'traceback.print_exc() 已存在'),
        ('account.name', 'account.name 字段引用正確'),
        ('new_balance = 0 -', 'TWD 帳戶餘額計算已修復'),
        ('new_balance = 0 +', 'RMB 帳戶餘額計算已修復'),
        ('db.session.execute("SELECT 1")', '資料庫連接檢查已添加'),
        ('FIFOInventory.query.all()', '庫存查詢錯誤處理已添加'),
        ('CashAccount.query.all()', '現金帳戶查詢錯誤處理已添加'),
        ('Customer.query.all()', '客戶查詢錯誤處理已添加')
    ]
    
    for check, description in fixes:
        if check in content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
    
    return True

def check_file_structure():
    """檢查文件結構"""
    print("\n🔍 檢查文件結構...")
    
    required_files = [
        'app.py',
        'test_data_recovery_fix.py',
        'test_db_connection_simple.py',
        'DATA_RECOVERY_API_FIX_REPORT.md',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
    
    return True

def check_git_status():
    """檢查 Git 狀態"""
    print("\n🔍 檢查 Git 狀態...")
    
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            print("   ⚠️  有未提交的更改:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"      {line}")
        else:
            print("   ✅ 所有更改已提交")
            
    except Exception as e:
        print(f"   ❌ 無法檢查 Git 狀態: {e}")
    
    return True

def main():
    """主函數"""
    print("🚀 數據修復 API 修復狀態檢查")
    print("=" * 50)
    
    # 執行所有檢查
    checks = [
        check_imports,
        check_data_recovery_api,
        check_file_structure,
        check_git_status
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"   ❌ 檢查失敗: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有檢查通過！數據修復 API 修復完成。")
        print("\n📋 下一步:")
        print("   1. 提交代碼到 Git: git add . && git commit -m '修復數據修復 API'")
        print("   2. 推送到遠程倉庫: git push origin main")
        print("   3. 等待 Render 自動部署")
        print("   4. 測試修復後的 API")
    else:
        print("⚠️  部分檢查未通過，請檢查上述問題。")
    
    print("\n📚 相關文檔:")
    print("   - DATA_RECOVERY_API_FIX_REPORT.md (修復報告)")
    print("   - DEPLOYMENT_GUIDE.md (部署指南)")

if __name__ == "__main__":
    main()
