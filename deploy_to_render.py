#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from datetime import datetime

def deploy_to_render():
    """部署到Render的完整流程"""
    print("=== RMB銷售系統部署到Render ===")
    print(f"部署時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 檢查Git狀態
    print("1. 檢查Git狀態:")
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            if result.stdout.strip():
                print("   發現未提交的變更:")
                print(f"   {result.stdout}")
                print("   建議先提交所有變更:")
                print("   git add .")
                print("   git commit -m 'Deploy: 修正利潤計算邏輯'")
                print("   git push")
            else:
                print("   [OK] 工作目錄乾淨，沒有未提交的變更")
        else:
            print("   [WARNING] Git狀態檢查失敗")
    except FileNotFoundError:
        print("   [WARNING] Git未安裝或不在PATH中")
    
    print()
    
    # 2. 檢查當前分支
    print("2. 檢查當前分支:")
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            print(f"   當前分支: {current_branch}")
            if current_branch != 'main':
                print(f"   [WARNING] 建議在main分支部署")
        else:
            print("   [WARNING] 無法獲取當前分支")
    except FileNotFoundError:
        print("   [WARNING] Git未安裝")
    
    print()
    
    # 3. 生成部署配置
    print("3. 生成部署配置:")
    
    # 檢查render.yaml
    if os.path.exists('render.yaml'):
        print("   [OK] render.yaml 已存在")
        
        # 讀取並顯示配置
        with open('render.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
            print("   當前配置:")
            print("   " + "\n   ".join(content.split('\n')[:10]))
            print("   ...")
    else:
        print("   [ERROR] render.yaml 不存在")
        return
    
    print()
    
    # 4. 檢查環境變量配置
    print("4. 環境變量配置:")
    print("   需要在Render Dashboard中設置以下環境變量:")
    print("   - FLASK_ENV=production")
    print("   - SECRET_KEY=<生成隨機密鑰>")
    print("   - DATABASE_URL=<PostgreSQL連接字符串>")
    print()
    print("   生成SECRET_KEY:")
    import secrets
    secret_key = secrets.token_hex(32)
    print(f"   SECRET_KEY={secret_key}")
    
    print()
    
    # 5. 部署步驟
    print("5. Render部署步驟:")
    print("   步驟1: 登入Render Dashboard (https://dashboard.render.com)")
    print("   步驟2: 點擊 'New +' -> 'Web Service'")
    print("   步驟3: 連接GitHub倉庫")
    print("   步驟4: 配置服務:")
    print("      - Name: rmb-sales-system")
    print("      - Environment: Python 3")
    print("      - Build Command: pip install -r requirements.txt")
    print("      - Start Command: gunicorn app:app")
    print("   步驟5: 設置環境變量")
    print("   步驟6: 點擊 'Create Web Service'")
    print("   步驟7: 等待部署完成")
    
    print()
    
    # 6. 部署後檢查
    print("6. 部署後檢查:")
    print("   - 檢查服務狀態是否為 'Live'")
    print("   - 訪問應用程序URL")
    print("   - 測試登入功能")
    print("   - 檢查數據庫連接")
    print("   - 測試主要功能")
    
    print()
    
    # 7. 數據庫遷移
    print("7. 數據庫遷移:")
    print("   如果使用PostgreSQL，需要:")
    print("   1. 在Render Dashboard設置DATABASE_URL")
    print("   2. 運行數據庫遷移:")
    print("      flask db upgrade")
    print("   3. 或者手動創建表結構")
    
    print()
    print("=== 部署準備完成 ===")
    print()
    print("下一步:")
    print("1. 提交代碼到Git: git add . && git commit -m 'Deploy' && git push")
    print("2. 在Render Dashboard創建Web Service")
    print("3. 設置環境變量")
    print("4. 部署並測試")

def generate_deploy_commands():
    """生成部署命令"""
    print("\n=== 快速部署命令 ===")
    print()
    print("1. 提交代碼:")
    print("   git add .")
    print("   git commit -m 'Deploy: 修正利潤計算邏輯和現金管理API'")
    print("   git push origin main")
    print()
    print("2. 在Render Dashboard設置環境變量:")
    print("   FLASK_ENV=production")
    print("   SECRET_KEY=<上面生成的密鑰>")
    print("   DATABASE_URL=<PostgreSQL URL>")
    print()
    print("3. 部署完成後測試:")
    print("   curl https://your-app-name.onrender.com/")
    print("   或直接在瀏覽器訪問")

if __name__ == "__main__":
    deploy_to_render()
    generate_deploy_commands()
