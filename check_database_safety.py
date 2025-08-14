#!/usr/bin/env python3
"""
資料庫安全檢查腳本
檢查代碼中是否有危險的資料庫操作
"""

import os
import re
import glob

def check_file_safety(file_path):
    """檢查單個文件的安全性"""
    dangerous_patterns = [
        # 危險的資料庫操作
        r'db\.drop_all\(\)',
        r'db\.create_all\(\)',  # 在某些情況下可能危險
        r'DROP TABLE',
        r'TRUNCATE TABLE',
        r'DELETE FROM \w+',  # 刪除整個表格
        r'DELETE \*',
        r'clear.*data',
        r'clear.*all',
        r'remove.*all',
        r'wipe.*data',
        r'reset.*database',
        r'purge.*data',
        
        # 危險的文件操作
        r'os\.remove.*\.db',
        r'os\.unlink.*\.db',
        r'shutil\.rmtree',
        r'rm -rf',
        
        # 危險的 SQL 操作
        r'EXECUTE.*DROP',
        r'EXECUTE.*DELETE',
        r'EXECUTE.*TRUNCATE',
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        for pattern in dangerous_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1].strip()
                issues.append({
                    'pattern': pattern,
                    'line': line_num,
                    'content': line_content,
                    'severity': 'HIGH' if 'DROP' in pattern or 'DELETE' in pattern else 'MEDIUM'
                })
        
        return issues
        
    except Exception as e:
        return [{'error': str(e)}]

def check_python_files():
    """檢查所有 Python 文件"""
    python_files = glob.glob('*.py') + glob.glob('**/*.py', recursive=True)
    
    all_issues = {}
    
    for file_path in python_files:
        # 跳過備份目錄和虛擬環境
        if 'database_backups' in file_path or 'venv' in file_path or '__pycache__' in file_path:
            continue
            
        issues = check_file_safety(file_path)
        if issues:
            all_issues[file_path] = issues
    
    return all_issues

def check_html_files():
    """檢查所有 HTML 文件中的危險操作"""
    html_files = glob.glob('templates/**/*.html', recursive=True)
    
    dangerous_html_patterns = [
        r'onclick.*confirm.*delete',
        r'onclick.*confirm.*remove',
        r'onclick.*confirm.*clear',
        r'action.*delete',
        r'action.*remove',
        r'action.*clear',
    ]
    
    all_issues = {}
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            for pattern in dangerous_html_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()
                    issues.append({
                        'pattern': pattern,
                        'line': line_num,
                        'content': line_content,
                        'severity': 'MEDIUM'
                    })
            
            if issues:
                all_issues[file_path] = issues
                
        except Exception as e:
            all_issues[file_path] = [{'error': str(e)}]
    
    return all_issues

def main():
    """主函數"""
    print("🛡️  RMB銷售系統資料庫安全檢查")
    print("=" * 50)
    
    print("\n🔍 檢查 Python 文件...")
    python_issues = check_python_files()
    
    print("\n🔍 檢查 HTML 文件...")
    html_issues = check_html_files()
    
    # 顯示結果
    total_issues = 0
    
    if python_issues:
        print(f"\n⚠️  發現 {len(python_issues)} 個 Python 文件有潛在危險:")
        for file_path, issues in python_issues.items():
            print(f"\n📁 {file_path}:")
            for issue in issues:
                if 'error' in issue:
                    print(f"   ❌ 讀取錯誤: {issue['error']}")
                else:
                    severity_icon = "🔴" if issue['severity'] == 'HIGH' else "🟡"
                    print(f"   {severity_icon} 第 {issue['line']} 行: {issue['content']}")
                    print(f"      危險模式: {issue['pattern']}")
                    print(f"      危險等級: {issue['severity']}")
                total_issues += 1
    
    if html_issues:
        print(f"\n⚠️  發現 {len(html_issues)} 個 HTML 文件有潛在危險:")
        for file_path, issues in html_issues.items():
            print(f"\n📁 {file_path}:")
            for issue in issues:
                if 'error' in issue:
                    print(f"   ❌ 讀取錯誤: {issue['error']}")
                else:
                    print(f"   🟡 第 {issue['line']} 行: {issue['content']}")
                    print(f"      危險模式: {issue['pattern']}")
                    print(f"      危險等級: {issue['severity']}")
                total_issues += 1
    
    if not python_issues and not html_issues:
        print("\n✅ 沒有發現明顯的危險代碼！")
    else:
        print(f"\n📊 總共發現 {total_issues} 個潛在問題")
        
        # 提供建議
        print("\n💡 安全建議:")
        print("1. 檢查所有標記為 HIGH 危險等級的代碼")
        print("2. 確保資料庫操作有適當的確認機制")
        print("3. 定期備份資料庫")
        print("4. 在生產環境中謹慎使用管理員權限")
        print("5. 考慮添加資料庫操作日誌")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
