#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的數據庫備份腳本
"""

import os
import shutil
from datetime import datetime

def create_simple_backup():
    """創建簡單備份"""
    try:
        print("🛡️ 開始創建數據庫備份...")
        
        # 檢查數據庫文件
        db_paths = [
            "instance/sales_system_v4.db",
            "sales_system_v4.db"
        ]
        
        db_file = None
        for path in db_paths:
            if os.path.exists(path):
                db_file = path
                break
        
        if not db_file:
            print("❌ 找不到數據庫文件！")
            return False
        
        print(f"✅ 找到數據庫文件: {db_file}")
        
        # 創建備份目錄
        backup_dir = "recovery_backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成備份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 複製文件
        shutil.copy2(db_file, backup_path)
        
        # 獲取文件大小
        size_mb = os.path.getsize(backup_path) / (1024*1024)
        
        print(f"✅ 備份創建成功！")
        print(f"📁 備份文件: {backup_path}")
        print(f"📊 備份大小: {size_mb:.2f} MB")
        
        # 創建備份信息文件
        info_file = os.path.join(backup_dir, f"backup_{timestamp}_info.txt")
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("數據庫備份信息\n")
            f.write("="*30 + "\n")
            f.write(f"備份時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"備份文件: {backup_name}\n")
            f.write(f"原始文件: {db_file}\n")
            f.write(f"備份大小: {size_mb:.2f} MB\n")
            f.write("\n恢復方法:\n")
            f.write("1. 停止應用程序\n")
            f.write("2. 複製備份文件到原位置\n")
            f.write("3. 重啟應用程序\n")
        
        print(f"📄 備份信息: {info_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🛡️ 簡單數據庫備份工具")
    print("="*30)
    
    success = create_simple_backup()
    
    if success:
        print("\n🎉 備份完成！現在您可以安全地執行數據修復了。")
        print("\n📋 下一步操作:")
        print("   1. 訪問修復頁面: /admin_data_recovery")
        print("   2. 檢查數據狀態")
        print("   3. 執行數據修復")
    else:
        print("\n❌ 備份失敗，請檢查錯誤信息")
