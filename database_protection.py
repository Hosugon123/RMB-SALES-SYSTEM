#!/usr/bin/env python3
"""
資料庫保護機制
防止意外清空或刪除資料庫
"""

import os
import shutil
import sqlite3
from datetime import datetime
import json

class DatabaseProtector:
    def __init__(self, db_path="instance/sales_system_v4.db"):
        self.db_path = db_path
        self.backup_dir = "database_backups"
        self.protection_file = "database_protection.json"
        
        # 確保備份目錄存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 載入保護配置
        self.load_protection_config()
    
    def load_protection_config(self):
        """載入資料庫保護配置"""
        if os.path.exists(self.protection_file):
            with open(self.protection_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # 預設配置
            self.config = {
                "protection_enabled": True,
                "auto_backup": True,
                "backup_interval_hours": 24,
                "max_backups": 10,
                "last_backup": None,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            self.save_protection_config()
    
    def save_protection_config(self):
        """保存保護配置"""
        with open(self.protection_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def check_database_exists(self):
        """檢查資料庫是否存在"""
        return os.path.exists(self.db_path)
    
    def get_database_info(self):
        """獲取資料庫信息"""
        if not self.check_database_exists():
            return None
        
        try:
            # 獲取文件信息
            stat = os.stat(self.db_path)
            size_mb = stat.st_size / (1024 * 1024)
            
            # 連接資料庫獲取表格信息
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 獲取表格列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 獲取每個表格的記錄數
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except:
                    table_counts[table] = 0
            
            conn.close()
            
            return {
                "exists": True,
                "size_mb": round(size_mb, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "tables": tables,
                "table_counts": table_counts,
                "total_records": sum(table_counts.values())
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_backup(self, description="手動備份"):
        """創建資料庫備份"""
        if not self.check_database_exists():
            print("❌ 資料庫文件不存在，無法備份")
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}_{description.replace(' ', '_')}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 複製資料庫文件
            shutil.copy2(self.db_path, backup_path)
            
            # 更新配置
            self.config["last_backup"] = datetime.now().isoformat()
            self.save_protection_config()
            
            print(f"✅ 資料庫備份成功: {backup_name}")
            print(f"   備份路徑: {backup_path}")
            print(f"   備份大小: {os.path.getsize(backup_path) / (1024*1024):.2f} MB")
            
            # 清理舊備份
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return False
    
    def cleanup_old_backups(self):
        """清理舊的備份文件"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改時間排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 保留最新的備份
            if len(backup_files) > self.config["max_backups"]:
                files_to_delete = backup_files[self.config["max_backups"]:]
                for file_path, _ in files_to_delete:
                    os.remove(file_path)
                    print(f"🗑️  刪除舊備份: {os.path.basename(file_path)}")
                    
        except Exception as e:
            print(f"⚠️  清理舊備份時出錯: {e}")
    
    def restore_backup(self, backup_name):
        """從備份恢復資料庫"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            print(f"❌ 備份文件不存在: {backup_name}")
            return False
        
        try:
            # 創建當前資料庫的備份（以防萬一）
            self.create_backup("恢復前的安全備份")
            
            # 恢復資料庫
            shutil.copy2(backup_path, self.db_path)
            
            print(f"✅ 資料庫恢復成功: {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ 恢復失敗: {e}")
            return False
    
    def list_backups(self):
        """列出所有備份"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    stat = os.stat(file_path)
                    size_mb = stat.st_size / (1024 * 1024)
                    backup_files.append({
                        "name": file,
                        "size_mb": round(size_mb, 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按修改時間排序
            backup_files.sort(key=lambda x: x["modified"], reverse=True)
            
            return backup_files
            
        except Exception as e:
            print(f"❌ 列出備份時出錯: {e}")
            return []
    
    def enable_protection(self):
        """啟用資料庫保護"""
        self.config["protection_enabled"] = True
        self.save_protection_config()
        print("✅ 資料庫保護已啟用")
    
    def disable_protection(self):
        """禁用資料庫保護（謹慎使用）"""
        self.config["protection_enabled"] = False
        self.save_protection_config()
        print("⚠️  資料庫保護已禁用（請謹慎操作）")
    
    def show_status(self):
        """顯示保護狀態"""
        print("=" * 50)
        print("🛡️  資料庫保護狀態")
        print("=" * 50)
        
        # 保護配置
        print(f"保護狀態: {'✅ 已啟用' if self.config['protection_enabled'] else '❌ 已禁用'}")
        print(f"自動備份: {'✅ 已啟用' if self.config['auto_backup'] else '❌ 已禁用'}")
        print(f"備份間隔: {self.config['backup_interval_hours']} 小時")
        print(f"最大備份數: {self.config['max_backups']}")
        
        if self.config['last_backup']:
            print(f"最後備份: {self.config['last_backup']}")
        else:
            print("最後備份: 從未備份")
        
        print()
        
        # 資料庫狀態
        db_info = self.get_database_info()
        if db_info and "error" not in db_info:
            print("📊 資料庫狀態:")
            print(f"   文件大小: {db_info['size_mb']} MB")
            print(f"   最後修改: {db_info['modified']}")
            print(f"   表格數量: {len(db_info['tables'])}")
            print(f"   總記錄數: {db_info['total_records']}")
            
            print("\n📋 表格詳情:")
            for table in db_info['tables']:
                count = db_info['table_counts'].get(table, 0)
                print(f"   {table}: {count} 條記錄")
        else:
            print("❌ 無法獲取資料庫信息")
        
        print()
        
        # 備份狀態
        backups = self.list_backups()
        print(f"💾 備份狀態 ({len(backups)} 個):")
        for backup in backups[:5]:  # 只顯示最新的5個
            print(f"   {backup['name']} ({backup['size_mb']} MB) - {backup['modified']}")
        
        if len(backups) > 5:
            print(f"   ... 還有 {len(backups) - 5} 個備份")
        
        print("=" * 50)

def main():
    """主函數"""
    protector = DatabaseProtector()
    
    print("🛡️  RMB銷售系統資料庫保護工具")
    print("=" * 40)
    
    while True:
        print("\n請選擇操作:")
        print("1. 顯示保護狀態")
        print("2. 創建備份")
        print("3. 列出備份")
        print("4. 恢復備份")
        print("5. 啟用保護")
        print("6. 禁用保護")
        print("7. 退出")
        
        choice = input("\n請輸入選項 (1-7): ").strip()
        
        if choice == "1":
            protector.show_status()
        
        elif choice == "2":
            description = input("請輸入備份描述 (可選): ").strip()
            if not description:
                description = "手動備份"
            protector.create_backup(description)
        
        elif choice == "3":
            backups = protector.list_backups()
            if backups:
                print(f"\n📋 找到 {len(backups)} 個備份:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['name']} ({backup['size_mb']} MB) - {backup['modified']}")
            else:
                print("📋 沒有找到備份文件")
        
        elif choice == "4":
            backups = protector.list_backups()
            if backups:
                print(f"\n📋 可用的備份:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['name']} ({backup['size_mb']} MB) - {backup['modified']}")
                
                try:
                    backup_index = int(input("\n請選擇要恢復的備份編號: ")) - 1
                    if 0 <= backup_index < len(backups):
                        backup_name = backups[backup_index]['name']
                        confirm = input(f"確定要恢復備份 {backup_name} 嗎？這將覆蓋當前資料庫！(yes/no): ")
                        if confirm.lower() == 'yes':
                            protector.restore_backup(backup_name)
                        else:
                            print("❌ 取消恢復操作")
                    else:
                        print("❌ 無效的備份編號")
                except ValueError:
                    print("❌ 請輸入有效的數字")
            else:
                print("📋 沒有可用的備份")
        
        elif choice == "5":
            protector.enable_protection()
        
        elif choice == "6":
            confirm = input("確定要禁用資料庫保護嗎？這可能導致資料丟失！(yes/no): ")
            if confirm.lower() == 'yes':
                protector.disable_protection()
            else:
                print("❌ 取消禁用操作")
        
        elif choice == "7":
            print("👋 再見！")
            break
        
        else:
            print("❌ 無效的選項，請重新選擇")

if __name__ == "__main__":
    main()
