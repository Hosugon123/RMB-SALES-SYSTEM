#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
運行資料庫遷移腳本
"""

import sys
import os

# 添加當前目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask_migrate import upgrade, downgrade, current, history
    from app import app, db
    print("✅ 成功導入所有必要的模組")
    
    # 創建應用程式上下文
    with app.app_context():
        print("✅ 成功創建應用程式上下文")
        
        # 檢查當前遷移狀態
        try:
            current_revision = current()
            print(f"✅ 當前遷移版本: {current_revision}")
        except Exception as e:
            print(f"❌ 獲取當前遷移版本失敗: {e}")
        
        # 檢查遷移歷史
        try:
            migration_history = history()
            print(f"✅ 遷移歷史記錄數量: {len(migration_history)}")
            for migration in migration_history:
                print(f"   - {migration.revision}: {migration.comment}")
        except Exception as e:
            print(f"❌ 獲取遷移歷史失敗: {e}")
        
        # 嘗試升級到最新版本
        try:
            print("🔄 開始升級資料庫...")
            upgrade()
            print("✅ 資料庫升級成功")
        except Exception as e:
            print(f"❌ 資料庫升級失敗: {e}")
        
        # 再次檢查當前狀態
        try:
            current_revision = current()
            print(f"✅ 升級後遷移版本: {current_revision}")
        except Exception as e:
            print(f"❌ 獲取升級後遷移版本失敗: {e}")
        
        print("\n🎯 遷移腳本執行完成")
        
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保已安裝 flask-migrate: pip install flask-migrate")
    sys.exit(1)
except Exception as e:
    print(f"❌ 遷移過程中發生錯誤: {e}")
    sys.exit(1)

