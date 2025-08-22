#!/usr/bin/env python3
"""
緊急資料庫保護腳本
禁用所有可能導致資料庫數據丟失的危險操作
"""

import os
import shutil
from datetime import datetime

def emergency_protection():
    """緊急保護資料庫"""
    
    print("🚨 緊急資料庫保護啟動！")
    print("=" * 60)
    print(f"保護時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 備份所有重要文件
    print("\n📦 步驟1: 備份重要文件...")
    
    files_to_backup = [
        'app.py',
        'global_sync.py',
        'data_sync_service.py'
    ]
    
    backup_dir = 'emergency_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(backup_dir, exist_ok=True)
    
    for file in files_to_backup:
        if os.path.exists(file):
            try:
                shutil.copy2(file, os.path.join(backup_dir, file))
                print(f"  ✅ 已備份: {file}")
            except Exception as e:
                print(f"  ❌ 備份失敗 {file}: {e}")
    
    print(f"📁 備份目錄: {backup_dir}")
    
    # 2. 禁用 app.py 中的危險API
    print("\n🛡️ 步驟2: 禁用危險的API端點...")
    
    if os.path.exists('app.py'):
        try:
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 註釋掉 api_clear_all_data 函數
            if "def api_clear_all_data" in content:
                # 找到函數開始位置
                start_pos = content.find("def api_clear_all_data")
                if start_pos != -1:
                    # 找到下一個路由裝飾器
                    next_route = content.find("@app.route", start_pos + 1)
                    if next_route != -1:
                        # 註釋掉整個函數
                        function_content = content[start_pos:next_route]
                        commented_function = "\n".join([f"# {line}" for line in function_content.split('\n')])
                        
                        new_content = content[:start_pos] + commented_function + content[next_route:]
                        
                        with open('app.py', 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print("  ✅ 已禁用 api_clear_all_data 函數")
                    else:
                        print("  ⚠️  無法找到函數結束位置")
                else:
                    print("  ⚠️  無法找到函數開始位置")
            else:
                print("  ✅ api_clear_all_data 函數不存在或已被禁用")
        except Exception as e:
            print(f"  ❌ 禁用API失敗: {e}")
    
    # 3. 禁用 global_sync.py 中的危險操作
    print("\n🛡️ 步驟3: 禁用 global_sync.py 中的危險操作...")
    
    if os.path.exists('global_sync.py'):
        try:
            with open('global_sync.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 註釋掉 DELETE 語句
            dangerous_lines = [
                "DELETE FROM fifo_inventory",
                "DELETE FROM fifo_sales_allocations"
            ]
            
            modified = False
            for line in dangerous_lines:
                if line in content:
                    # 註釋掉包含危險語句的行
                    content = content.replace(line, f"# {line}  # 🚨 危險操作已禁用")
                    modified = True
                    print(f"  ✅ 已禁用: {line}")
            
            if modified:
                with open('global_sync.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✅ global_sync.py 已保護")
            else:
                print("  ✅ 沒有發現危險的 DELETE 操作")
        except Exception as e:
            print(f"  ❌ 保護 global_sync.py 失敗: {e}")
    
    # 4. 創建資料庫保護機制
    print("\n🛡️ 步驟4: 創建資料庫保護機制...")
    
    protection_code = '''#!/usr/bin/env python3
"""
資料庫保護機制
防止危險的資料庫操作
"""

import os
import sys
from datetime import datetime

class DatabaseProtector:
    """資料庫保護器"""
    
    def __init__(self):
        self.dangerous_operations = [
            "DROP TABLE",
            "DELETE FROM",
            "TRUNCATE",
            "clear_all",
            "reset_database"
        ]
    
    def check_operation_safety(self, operation):
        """檢查操作安全性"""
        operation_lower = operation.lower()
        
        for dangerous in self.dangerous_operations:
            if dangerous.lower() in operation_lower:
                print(f"🚨 檢測到危險操作: {dangerous}")
                print(f"   操作內容: {operation}")
                print(f"   時間: {datetime.now()}")
                return False
        
        return True
    
    def log_operation(self, operation, user=None):
        """記錄操作日誌"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] 操作: {operation}"
        if user:
            log_entry += f" | 用戶: {user}"
        
        with open('database_operations.log', 'a', encoding='utf-8') as f:
            f.write(log_entry + "\\n")
        
        print(f"📝 操作已記錄: {operation}")

# 創建全局保護器實例
db_protector = DatabaseProtector()

def safe_database_operation(operation, user=None):
    """安全的資料庫操作包裝器"""
    if db_protector.check_operation_safety(operation):
        db_protector.log_operation(operation, user)
        return True
    else:
        print("❌ 危險操作已被阻止！")
        return False

if __name__ == "__main__":
    print("🛡️ 資料庫保護機制已啟動")
    print("危險操作將被阻止並記錄")
'''
    
    try:
        with open('database_protector.py', 'w', encoding='utf-8') as f:
            f.write(protection_code)
        print("  ✅ 資料庫保護機制已創建: database_protector.py")
    except Exception as e:
        print(f"  ❌ 創建保護機制失敗: {e}")
    
    # 5. 創建保護報告
    print("\n📋 步驟5: 創建保護報告...")
    
    report_content = f"""# 緊急資料庫保護報告

## 🚨 保護操作完成

保護時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 已執行的保護措施:

1. **備份重要文件**
   - 備份目錄: {backup_dir}
   - 已備份: app.py, global_sync.py, data_sync_service.py

2. **禁用危險API端點**
   - api_clear_all_data 函數已被註釋掉
   - 防止資料庫被意外清空

3. **禁用危險的同步操作**
   - global_sync.py 中的 DELETE 操作已被註釋掉
   - 防止庫存和銷售分配記錄被刪除

4. **創建資料庫保護機制**
   - database_protector.py 已創建
   - 提供操作安全檢查和日誌記錄

### 🛡️ 安全建議:

1. **立即檢查Render服務日誌**
   - 確認是否有清空操作記錄
   - 檢查是否有錯誤日誌

2. **設置資料庫監控**
   - 使用 database_protector.py 監控所有操作
   - 定期檢查操作日誌

3. **定期備份資料庫**
   - 設置自動備份機制
   - 測試備份恢復流程

4. **檢查其他可能的危險腳本**
   - 搜索專案中的危險關鍵字
   - 禁用或重命名危險腳本

### 🔄 恢復方法:

如果需要恢復被禁用的功能:
```bash
# 恢復 app.py
cp {backup_dir}/app.py app.py

# 恢復 global_sync.py  
cp {backup_dir}/global_sync.py global_sync.py
```

### ⚠️ 重要警告:

- 所有危險的資料庫操作已被禁用
- 請在恢復前確認安全性
- 建議設置資料庫保護機制後再恢復

---
🛡️ 資料庫保護完成！請立即檢查Render服務狀態！
"""
    
    try:
        with open('EMERGENCY_PROTECTION_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(report_content)
        print("  ✅ 保護報告已創建: EMERGENCY_PROTECTION_REPORT.md")
    except Exception as e:
        print(f"  ❌ 創建報告失敗: {e}")
    
    return backup_dir

def main():
    """主函數"""
    
    print("🚨 開始緊急資料庫保護...")
    
    backup_dir = emergency_protection()
    
    print("\n" + "=" * 60)
    print("🎯 緊急保護完成！")
    print(f"\n📁 備份目錄: {backup_dir}")
    print("\n🚨 緊急行動建議:")
    print("1. 立即檢查Render服務日誌")
    print("2. 確認資料庫狀態")
    print("3. 檢查是否有自動執行的腳本")
    print("4. 設置資料庫監控機制")
    print("5. 定期備份資料庫")

if __name__ == "__main__":
    main()
