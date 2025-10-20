#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
from datetime import datetime

def check_deployment_readiness():
    """檢查部署準備狀態"""
    print("=== RMB銷售系統部署檢查 ===")
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 檢查必要文件
    print("1. 檢查必要文件:")
    required_files = [
        'app.py',
        'requirements.txt',
        'render.yaml',
        'instance/sales_system_v4.db'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   [OK] {file_path}")
        else:
            print(f"   [MISSING] {file_path}")
    
    print()
    
    # 2. 檢查數據庫
    print("2. 檢查數據庫:")
    db_path = 'instance/sales_system_v4.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查關鍵表
            key_tables = ['sales_records', 'ledger_entries', 'cash_accounts', 'customers']
            for table in key_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count} records")
                except Exception as e:
                    print(f"   {table}: ERROR - {e}")
            
            conn.close()
            print("   [OK] Database connection successful")
        except Exception as e:
            print(f"   [ERROR] Database check failed: {e}")
    else:
        print("   [ERROR] Database file not found")
    
    print()
    
    # 3. 檢查Python依賴
    print("3. 檢查Python依賴:")
    dependencies = ['flask', 'sqlalchemy', 'gunicorn']
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"   [OK] {dep} {version}")
        except ImportError:
            print(f"   [MISSING] {dep}")
    
    print()
    
    # 4. 檢查應用程序
    print("4. 檢查應用程序:")
    try:
        os.environ['FLASK_ENV'] = 'production'
        sys.path.append('.')
        from app import app
        print("   [OK] Application import successful")
        
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"   [OK] Found {len(routes)} routes")
        
    except Exception as e:
        print(f"   [ERROR] Application check failed: {e}")
    
    print()
    
    # 5. 部署建議
    print("5. 部署建議:")
    print("   Render部署步驟:")
    print("   1. 確保所有文件已提交到Git")
    print("   2. 在Render Dashboard創建新的Web Service")
    print("   3. 連接GitHub倉庫")
    print("   4. 設置環境變量:")
    print("      - FLASK_ENV=production")
    print("      - SECRET_KEY=<random key>")
    print("      - DATABASE_URL=<PostgreSQL URL>")
    print("   5. 設置構建命令: pip install -r requirements.txt")
    print("   6. 設置啟動命令: gunicorn app:app")
    print("   7. 部署並測試")
    
    print()
    print("=== 檢查完成 ===")

if __name__ == "__main__":
    check_deployment_readiness()