#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據修復前備份腳本
專門為數據修復操作創建安全備份
"""

import os
import sys
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def create_recovery_backup():
    """創建數據修復前的安全備份"""
    
    print("🛡️ 開始創建數據修復前安全備份...")
    print("="*50)
    
    # 檢查當前目錄
    current_dir = Path.cwd()
    print(f"📍 當前目錄: {current_dir}")
    
    # 檢查數據庫文件
    db_paths = [
        current_dir / "instance" / "sales_system_v4.db",
        current_dir / "sales_system_v4.db"
    ]
    
    db_file = None
    for path in db_paths:
        if path.exists():
            db_file = path
            break
    
    if not db_file:
        print("❌ 找不到數據庫文件！")
        print("請確保在正確的項目目錄中執行此腳本")
        return False
    
    print(f"✅ 找到數據庫文件: {db_file}")
    print(f"📊 數據庫大小: {db_file.stat().st_size / (1024*1024):.2f} MB")
    
    # 創建備份目錄
    backup_dir = current_dir / "recovery_backups"
    backup_dir.mkdir(exist_ok=True)
    print(f"📁 備份目錄: {backup_dir}")
    
    # 生成備份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"recovery_backup_{timestamp}"
    backup_file = backup_dir / f"{backup_name}.zip"
    
    print(f"📦 備份文件名: {backup_file.name}")
    
    try:
        # 創建備份
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加數據庫文件
            zipf.write(db_file, db_file.name)
            
            # 添加備份信息
            backup_info = {
                "backup_type": "recovery_backup",
                "created_at": datetime.now().isoformat(),
                "database_file": str(db_file),
                "database_size_mb": round(db_file.stat().st_size / (1024*1024), 2),
                "purpose": "數據修復前安全備份",
                "warning": "此備份包含修復前的原始數據，請妥善保管",
                "recovery_instructions": [
                    "1. 停止應用程序",
                    "2. 解壓備份文件",
                    "3. 替換數據庫文件",
                    "4. 重啟應用程序"
                ]
            }
            
            # 將備份信息寫入 JSON 文件
            info_file = backup_dir / f"{backup_name}_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 將信息文件也加入備份
            zipf.write(info_file, info_file.name)
            
            # 添加重要配置文件
            config_files = [
                "backup_config.json",
                "requirements.txt",
                "app.py"
            ]
            
            for config_file in config_files:
                config_path = current_dir / config_file
                if config_path.exists():
                    zipf.write(config_path, config_file)
                    print(f"   ✅ 已備份: {config_file}")
            
            # 添加模板文件
            templates_dir = current_dir / "templates"
            if templates_dir.exists():
                for template_file in templates_dir.glob("*.html"):
                    zipf.write(template_file, f"templates/{template_file.name}")
                    print(f"   ✅ 已備份: {template_file.name}")
        
        print(f"\n✅ 備份創建成功！")
        print(f"📁 備份文件: {backup_file}")
        print(f"📊 備份大小: {backup_file.stat().st_size / (1024*1024):.2f} MB")
        
        # 創建備份摘要
        summary_file = backup_dir / f"{backup_name}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*50 + "\n")
            f.write("🛡️ 數據修復前安全備份摘要\n")
            f.write("="*50 + "\n")
            f.write(f"備份時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"備份文件: {backup_file.name}\n")
            f.write(f"數據庫文件: {db_file.name}\n")
            f.write(f"數據庫大小: {backup_info['database_size_mb']} MB\n")
            f.write(f"備份大小: {backup_file.stat().st_size / (1024*1024):.2f} MB\n")
            f.write("\n⚠️ 重要提醒:\n")
            f.write("- 此備份包含修復前的原始數據\n")
            f.write("- 請妥善保管備份文件\n")
            f.write("- 修復完成後可以刪除此備份\n")
            f.write("\n🔄 恢復方法:\n")
            for instruction in backup_info['recovery_instructions']:
                f.write(f"  {instruction}\n")
        
        print(f"📄 備份摘要: {summary_file}")
        
        # 顯示備份目錄內容
        print(f"\n📁 備份目錄內容:")
        for file in backup_dir.iterdir():
            if file.is_file():
                size_mb = file.stat().st_size / (1024*1024)
                print(f"   - {file.name} ({size_mb:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ 備份創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_recovery_backups():
    """列出所有恢復備份"""
    backup_dir = Path.cwd() / "recovery_backups"
    
    if not backup_dir.exists():
        print("❌ 沒有找到恢復備份目錄")
        return
    
    print("📁 恢復備份列表:")
    print("="*50)
    
    backups = []
    for file in backup_dir.iterdir():
        if file.is_file() and file.suffix == '.zip':
            stat = file.stat()
            backups.append({
                'name': file.name,
                'size_mb': stat.st_size / (1024*1024),
                'created': datetime.fromtimestamp(stat.st_mtime)
            })
    
    if not backups:
        print("   📭 沒有找到恢復備份")
        return
    
    # 按創建時間排序
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    for i, backup in enumerate(backups, 1):
        print(f"{i:2d}. {backup['name']}")
        print(f"    大小: {backup['size_mb']:.2f} MB")
        print(f"    創建: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    """主函數"""
    print("🛡️ 數據修復前安全備份工具")
    print("="*50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_recovery_backups()
            return
        elif command == "help":
            print("使用方法:")
            print("  python backup_before_recovery.py          # 創建備份")
            print("  python backup_before_recovery.py list    # 列出備份")
            print("  python backup_before_recovery.py help    # 顯示幫助")
            return
        else:
            print(f"❌ 未知命令: {command}")
            print("使用 'python backup_before_recovery.py help' 查看幫助")
            return
    
    # 創建備份
    success = create_recovery_backup()
    
    if success:
        print("\n🎉 備份完成！現在您可以安全地執行數據修復了。")
        print("\n📋 下一步操作:")
        print("   1. 訪問修復頁面: /admin_data_recovery")
        print("   2. 檢查數據狀態")
        print("   3. 執行數據修復")
        print("\n⚠️ 重要提醒:")
        print("   - 備份文件已保存在 recovery_backups/ 目錄")
        print("   - 修復完成後可以刪除這些備份")
        print("   - 如果修復失敗，可以使用備份恢復數據")
    else:
        print("\n❌ 備份失敗，請檢查錯誤信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
