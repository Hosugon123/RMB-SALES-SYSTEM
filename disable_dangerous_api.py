#!/usr/bin/env python3
"""
禁用危險API端點的腳本
這個腳本會將危險的API端點重命名，防止被意外調用
"""

import os
import shutil
from datetime import datetime

def disable_dangerous_api():
    """禁用危險的API端點"""
    
    print("🚨 開始禁用危險的API端點...")
    print("=" * 60)
    
    # 備份原始app.py
    if os.path.exists('app.py'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'app_backup_{timestamp}.py'
        
        try:
            shutil.copy2('app.py', backup_file)
            print(f"✅ 已備份 app.py 到: {backup_file}")
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return False
    
    # 讀取app.py內容
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📖 讀取 app.py 完成")
        
        # 檢查是否包含危險的API端點
        dangerous_endpoints = [
            "/api/clear-all-data",
            "api_clear_all_data",
            "CONFIRM_CLEAR_ALL_DATA"
        ]
        
        found_dangerous = []
        for endpoint in dangerous_endpoints:
            if endpoint in content:
                found_dangerous.append(endpoint)
                print(f"  ⚠️  發現危險端點: {endpoint}")
        
        if not found_dangerous:
            print("✅ 沒有發現危險的API端點")
            return True
        
        # 禁用危險的API端點
        print("\n🛡️  開始禁用危險的API端點...")
        
        # 方法1：註釋掉整個函數
        if "def api_clear_all_data" in content:
            # 找到函數開始和結束位置
            start_marker = "def api_clear_all_data"
            end_marker = "@app.route(\"/api/settlement\""
            
            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker)
            
            if start_pos != -1 and end_pos != -1:
                # 註釋掉整個函數
                function_content = content[start_pos:end_pos]
                commented_function = "\n".join([f"# {line}" for line in function_content.split('\n')])
                
                new_content = content[:start_pos] + commented_function + content[end_pos:]
                
                # 寫入新內容
                with open('app.py', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ 已禁用 api_clear_all_data 函數")
                
                # 創建禁用說明文件
                create_disable_report(found_dangerous, backup_file)
                
                return True
            else:
                print("❌ 無法找到函數邊界")
                return False
        
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        return False

def create_disable_report(found_dangerous, backup_file):
    """創建禁用報告"""
    
    try:
        report_content = f"""# 危險API端點禁用報告

## 🚨 已禁用的危險端點

檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 發現的危險端點:
"""
        
        for endpoint in found_dangerous:
            report_content += f"- {endpoint}\n"
        
        report_content += f"""

### 備份文件:
- 原始 app.py: {backup_file}

### 禁用方法:
- 將整個 api_clear_all_data 函數註釋掉
- 防止被意外調用

### 安全建議:
1. 檢查Render服務日誌，確認是否有清空操作
2. 設置資料庫保護機制
3. 定期備份資料庫
4. 監控API調用日誌

### 恢復方法:
如果需要恢復，可以從備份文件恢復:
```bash
cp {backup_file} app.py
```

---
⚠️ 警告：此操作已禁用危險的資料庫清空功能！
"""
        
        with open('DANGEROUS_API_DISABLED_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("📄 禁用報告已保存到: DANGEROUS_API_DISABLED_REPORT.md")
        
    except Exception as e:
        print(f"⚠️  創建報告失敗: {e}")

def check_render_safety():
    """檢查Render安全性"""
    
    print("\n🌐 檢查Render安全性...")
    print("=" * 60)
    
    # 檢查是否有環境變數配置
    env_files = [".env", ".flaskenv", "config.py"]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  📋 環境配置文件: {env_file}")
            try:
                with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "FLASK_ENV" in content:
                        print(f"    ⚠️  包含 FLASK_ENV 配置")
                    if "DEBUG" in content:
                        print(f"    ⚠️  包含 DEBUG 配置")
            except Exception as e:
                print(f"    ❌ 無法讀取: {e}")
    
    # 檢查啟動腳本
    startup_scripts = ["start_app.py", "run_app.py", "simple_run.py"]
    
    for script in startup_scripts:
        if os.path.exists(script):
            print(f"  🚀 啟動腳本: {script}")
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "debug" in content.lower() or "development" in content.lower():
                        print(f"    ⚠️  可能包含開發模式配置")
            except Exception as e:
                print(f"    ❌ 無法讀取: {e}")

def main():
    """主函數"""
    
    print("🚀 開始禁用危險的API端點...")
    
    # 禁用危險的API端點
    if disable_dangerous_api():
        print("\n✅ 危險API端點禁用成功！")
    else:
        print("\n❌ 危險API端點禁用失敗！")
        return
    
    # 檢查Render安全性
    check_render_safety()
    
    print("\n" + "=" * 60)
    print("🎯 操作完成！")
    print("\n📋 下一步建議:")
    print("1. 檢查Render服務日誌")
    print("2. 確認資料庫狀態")
    print("3. 設置資料庫保護機制")
    print("4. 定期備份資料庫")

if __name__ == "__main__":
    main()
