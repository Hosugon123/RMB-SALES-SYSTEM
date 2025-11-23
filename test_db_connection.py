#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料庫連接和路徑
"""

import os
import sys

# 確保能夠導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_paths():
    """測試路徑設置"""
    print("=" * 80)
    print("測試資料庫路徑設置")
    print("=" * 80)
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, "instance")
    local_db_path = os.path.join(instance_path, "sales_system_v4.db")
    local_db_uri = "sqlite:///" + local_db_path
    
    print(f"\n工作目錄: {basedir}")
    print(f"Instance 目錄: {instance_path}")
    print(f"資料庫檔案路徑: {local_db_path}")
    print(f"資料庫 URI: {local_db_uri}")
    
    # 檢查目錄
    if os.path.exists(instance_path):
        print(f"\nInstance 目錄存在: 是")
    else:
        print(f"\nInstance 目錄存在: 否（將創建）")
        try:
            os.makedirs(instance_path, exist_ok=True)
            print("Instance 目錄已創建")
        except Exception as e:
            print(f"創建目錄失敗: {e}")
            return False
    
    # 檢查資料庫檔案
    if os.path.exists(local_db_path):
        print(f"資料庫檔案存在: 是")
        size = os.path.getsize(local_db_path)
        print(f"資料庫檔案大小: {size} 位元組")
    else:
        print(f"資料庫檔案存在: 否")
    
    return True

def test_app_import():
    """測試 app 導入"""
    print("\n" + "=" * 80)
    print("測試 app 模組導入")
    print("=" * 80)
    
    try:
        from app import app, db
        print("App 導入成功")
        print(f"資料庫 URI: {app.config.get('SQLALCHEMY_DATABASE_URI', '未設置')}")
        return True
    except Exception as e:
        print(f"App 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """測試資料庫連接"""
    print("\n" + "=" * 80)
    print("測試資料庫連接")
    print("=" * 80)
    
    try:
        from app import app, db
        
        with app.app_context():
            # 測試連接
            db.engine.connect()
            print("資料庫連接成功")
            
            # 檢查表
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"現有資料表數量: {len(tables)}")
            if tables:
                print(f"資料表: {', '.join(tables[:10])}")
                if len(tables) > 10:
                    print(f"... 還有 {len(tables) - 10} 個表")
            
            return True
    except Exception as e:
        print(f"資料庫連接失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n資料庫連接測試工具")
    print("此工具將測試路徑設置、模組導入和資料庫連接\n")
    
    success = True
    success = success and test_paths()
    success = success and test_app_import()
    
    if success:
        success = success and test_database_connection()
    
    print("\n" + "=" * 80)
    if success:
        print("所有測試通過！")
    else:
        print("部分測試失敗，請檢查上面的錯誤訊息")
    print("=" * 80)

