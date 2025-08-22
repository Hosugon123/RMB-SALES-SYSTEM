import os
import glob
from datetime import datetime

def check_dangerous_scripts():
    """檢查專案中可能存在的危險腳本"""
    
    print("🔍 檢查專案中的危險腳本...")
    print("=" * 60)
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 危險腳本模式
    dangerous_patterns = [
        # 資料庫清空腳本
        "clear_all_data.py",
        "clear_database.py", 
        "reset_database.py",
        "init_database.py",
        "initialize_database.py",
        "setup_database.py",
        
        # 資料清空腳本
        "clear_transactions.py",
        "clear_records.py",
        "wipe_data.py",
        "purge_data.py",
        
        # 快速清空腳本
        "quick_clear.py",
        "simple_clear.py",
        "fast_clear.py",
        
        # 初始化腳本
        "init.py",
        "setup.py",
        "bootstrap.py",
        
        # 其他危險腳本
        "drop_tables.py",
        "delete_all.py",
        "cleanup.py"
    ]
    
    # 檢查當前目錄和子目錄
    found_dangerous = []
    protected_dangerous = []
    suspicious_files = []
    
    print("\n📁 檢查危險腳本...")
    
    for pattern in dangerous_patterns:
        # 檢查當前目錄
        if os.path.exists(pattern):
            found_dangerous.append(pattern)
            print(f"  🔴 發現危險腳本: {pattern}")
        
        # 檢查帶有.DANGER擴展名的文件
        danger_file = pattern + ".DANGER"
        if os.path.exists(danger_file):
            protected_dangerous.append(danger_file)
            print(f"  🛡️  已保護的危險腳本: {danger_file}")
        
        # 檢查子目錄
        for root, dirs, files in os.walk('.'):
            for file in files:
                if pattern in file:
                    full_path = os.path.join(root, file)
                    if file == pattern:
                        found_dangerous.append(full_path)
                        print(f"  🔴 發現危險腳本: {full_path}")
                    elif file.endswith('.DANGER'):
                        protected_dangerous.append(full_path)
                        print(f"  🛡️  已保護的危險腳本: {full_path}")
    
    # 檢查可能包含危險內容的文件
    print("\n🔍 檢查可能包含危險內容的文件...")
    
    suspicious_keywords = [
        "DROP TABLE",
        "DELETE FROM",
        "TRUNCATE",
        "clear_all",
        "reset_database",
        "init_database",
        "setup_database"
    ]
    
    # 檢查Python文件
    python_files = glob.glob("**/*.py", recursive=True)
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for keyword in suspicious_keywords:
                    if keyword.lower() in content.lower():
                        suspicious_files.append((py_file, keyword))
                        print(f"  ⚠️  可疑文件: {py_file} (包含: {keyword})")
                        break
        except Exception as e:
            print(f"  ❌ 無法讀取文件 {py_file}: {e}")
    
    # 檢查啟動腳本
    print("\n🚀 檢查啟動腳本...")
    
    startup_scripts = [
        "app.py",
        "run_app.py", 
        "start_app.py",
        "main.py",
        "wsgi.py",
        "gunicorn.conf.py"
    ]
    
    for script in startup_scripts:
        if os.path.exists(script):
            print(f"  📋 啟動腳本: {script}")
            
            # 檢查是否包含危險的初始化代碼
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    if any(keyword.lower() in content.lower() for keyword in suspicious_keywords):
                        print(f"    ⚠️  包含可疑內容")
                        suspicious_files.append((script, "可疑啟動代碼"))
            except Exception as e:
                print(f"    ❌ 無法讀取: {e}")
    
    # 檢查requirements.txt和依賴
    print("\n📦 檢查依賴文件...")
    
    if os.path.exists("requirements.txt"):
        print("  📋 requirements.txt 存在")
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                content = f.read()
                if "flask-migrate" in content or "alembic" in content:
                    print("    ⚠️  包含資料庫遷移工具")
                if "sqlite3" in content:
                    print("    ⚠️  包含SQLite操作工具")
        except Exception as e:
            print(f"    ❌ 無法讀取: {e}")
    
    # 檢查migrations目錄
    if os.path.exists("migrations"):
        print("  📁 migrations目錄存在")
        migration_files = glob.glob("migrations/versions/*.py")
        print(f"    發現 {len(migration_files)} 個遷移文件")
        
        # 檢查最新的遷移文件
        if migration_files:
            latest_migration = max(migration_files, key=os.path.getctime)
            print(f"    最新遷移文件: {os.path.basename(latest_migration)}")
    
    # 生成檢查報告
    print("\n" + "=" * 60)
    print("📋 檢查報告")
    print("=" * 60)
    
    if found_dangerous:
        print(f"🔴 發現 {len(found_dangerous)} 個危險腳本:")
        for script in found_dangerous:
            print(f"  - {script}")
        print("\n🚨 建議立即處理這些危險腳本！")
    else:
        print("✅ 沒有發現未保護的危險腳本")
    
    if protected_dangerous:
        print(f"\n🛡️  發現 {len(protected_dangerous)} 個已保護的危險腳本:")
        for script in protected_dangerous:
            print(f"  - {script}")
    
    if suspicious_files:
        print(f"\n⚠️  發現 {len(suspicious_files)} 個可疑文件:")
        for file, reason in suspicious_files:
            print(f"  - {file}: {reason}")
    
    # 保存檢查結果
    save_check_report(found_dangerous, protected_dangerous, suspicious_files)
    
    print(f"\n📄 檢查報告已保存到: dangerous_scripts_report.txt")
    
    return found_dangerous, protected_dangerous, suspicious_files

def save_check_report(found_dangerous, protected_dangerous, suspicious_files):
    """保存檢查結果到文件"""
    
    try:
        with open('dangerous_scripts_report.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("危險腳本檢查報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("🔴 發現的危險腳本:\n")
            if found_dangerous:
                for script in found_dangerous:
                    f.write(f"  - {script}\n")
            else:
                f.write("  無\n")
            
            f.write(f"\n🛡️  已保護的危險腳本:\n")
            if protected_dangerous:
                for script in protected_dangerous:
                    f.write(f"  - {script}\n")
            else:
                f.write("  無\n")
            
            f.write(f"\n⚠️  可疑文件:\n")
            if suspicious_files:
                for file, reason in suspicious_files:
                    f.write(f"  - {file}: {reason}\n")
            else:
                f.write("  無\n")
            
            f.write(f"\n📋 總結:\n")
            f.write(f"  - 危險腳本: {len(found_dangerous)} 個\n")
            f.write(f"  - 已保護腳本: {len(protected_dangerous)} 個\n")
            f.write(f"  - 可疑文件: {len(suspicious_files)} 個\n")
            
            if found_dangerous:
                f.write(f"\n🚨 緊急建議:\n")
                f.write(f"  1. 立即刪除或重命名危險腳本\n")
                f.write(f"  2. 檢查這些腳本是否被自動執行\n")
                f.write(f"  3. 檢查Render服務日誌\n")
                f.write(f"  4. 設置資料庫保護機制\n")
        
    except Exception as e:
        print(f"⚠️  保存報告失敗: {e}")

def check_render_specific_issues():
    """檢查Render特定的問題"""
    
    print("\n🌐 檢查Render特定問題...")
    print("=" * 60)
    
    # 檢查是否有環境變數配置
    env_files = [".env", ".env.local", ".env.production", "config.py"]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  📋 環境配置文件: {env_file}")
            try:
                with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "DATABASE_URL" in content or "SQLALCHEMY_DATABASE_URI" in content:
                        print(f"    ⚠️  包含資料庫連接配置")
                    if "FLASK_ENV" in content or "ENVIRONMENT" in content:
                        print(f"    ⚠️  包含環境變數配置")
            except Exception as e:
                print(f"    ❌ 無法讀取: {e}")
    
    # 檢查是否有部署配置
    deploy_files = ["render.yaml", "Procfile", "runtime.txt", "build.sh"]
    
    for deploy_file in deploy_files:
        if os.path.exists(deploy_file):
            print(f"  🚀 部署配置文件: {deploy_file}")
    
    # 檢查是否有定時任務配置
    cron_files = ["crontab", "cron.txt", "scheduler.py", "tasks.py"]
    
    for cron_file in cron_files:
        if os.path.exists(cron_file):
            print(f"  ⏰ 定時任務文件: {cron_file}")
            try:
                with open(cron_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if any(keyword in content for keyword in ["clear", "reset", "init", "setup"]):
                        print(f"    ⚠️  包含可疑的定時任務")
            except Exception as e:
                print(f"    ❌ 無法讀取: {e}")

def main():
    """主函數"""
    
    print("🚀 開始檢查專案中的危險腳本...")
    
    # 檢查危險腳本
    found, protected, suspicious = check_dangerous_scripts()
    
    # 檢查Render特定問題
    check_render_specific_issues()
    
    print("\n" + "=" * 60)
    print("🎯 檢查完成！")
    
    if found:
        print("\n🚨 緊急行動建議:")
        print("1. 立即處理發現的危險腳本")
        print("2. 檢查Render服務日誌")
        print("3. 檢查是否有自動執行的腳本")
        print("4. 設置資料庫保護機制")
    else:
        print("\n✅ 沒有發現立即危險，但建議:")
        print("1. 檢查Render服務日誌")
        print("2. 檢查資料庫連接狀態")
        print("3. 設置定期備份機制")

if __name__ == "__main__":
    main()
