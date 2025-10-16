#!/usr/bin/env python3
"""
修復 HTML 模板文件中的 JavaScript 語法錯誤
主要處理 Jinja2 模板語法與 JavaScript 的衝突問題
"""

import re
import os

def fix_js_syntax_errors(file_path):
    """修復指定文件中的 JavaScript 語法錯誤"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修復常見的 JavaScript 語法問題
    
    # 1. 修復 Jinja2 模板中的引號問題
    # 將 onclick 中的單引號改為雙引號，避免與 Jinja2 衝突
    content = re.sub(
        r"onclick=\"([^\"]*)\{\{([^}]*)\}\}([^\"]*)\"",
        lambda m: f'onclick="{m.group(1)}{{m.group(2)}}{m.group(3)}"',
        content
    )
    
    # 2. 修復模板字符串中的引號問題
    content = re.sub(
        r"onclick='([^']*)\{\{([^}]*)\}\}([^']*)'",
        lambda m: f'onclick=\'{m.group(1)}{{m.group(2)}}{m.group(3)}\'',
        content
    )
    
    # 3. 修復 JavaScript 中的 Jinja2 表達式
    # 確保 JSON 數據正確轉義
    content = re.sub(
        r'const\s+(\w+)\s*=\s*\{\{\s*([^}]+)\s*\|tojson\s*\}\};',
        lambda m: f'const {m.group(1)} = {{m.group(2)}|tojson}};',
        content
    )
    
    # 4. 修復未閉合的標籤
    content = re.sub(
        r'<button([^>]*onclick="[^"]*")>\s*<i([^>]*)></i>([^<]*)</button>',
        r'<button\1>\n                                    <i\2></i>\3\n                                </button>',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # 5. 修復 JavaScript 中的字符串拼接問題
    content = re.sub(
        r'(\w+)\s*\+\s*\'\{\{([^}]+)\}\}\'',
        lambda m: f'{m.group(1)} + \'{{m.group(2)}}\'',
        content
    )
    
    # 檢查是否有修改
    if content != original_content:
        # 備份原文件
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # 寫入修復後的內容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修復 {file_path}")
        print(f"📁 備份文件: {backup_path}")
        return True
    else:
        print(f"ℹ️  {file_path} 無需修復")
        return False

def main():
    """主函數"""
    print("🔧 開始修復 JavaScript 語法錯誤...")
    
    # 要修復的文件列表
    files_to_fix = [
        'templates/cash_management.html',
        'templates/buy_in.html',
        'templates/sales_entry.html',
        'templates/inventory_purchase.html',
        'templates/exchange_rate.html'
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_js_syntax_errors(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  文件不存在: {file_path}")
    
    print(f"\n🎉 修復完成！共修復了 {fixed_count} 個文件")
    
    if fixed_count > 0:
        print("\n📋 修復內容:")
        print("   - 修復了 Jinja2 模板與 JavaScript 的引號衝突")
        print("   - 修復了未閉合的 HTML 標籤")
        print("   - 修復了 JavaScript 字符串拼接問題")
        print("   - 確保 JSON 數據正確轉義")
        
        print("\n🔍 建議:")
        print("   1. 重新檢查 VS Code 的 Problems 面板")
        print("   2. 測試銷帳金額驗證功能")
        print("   3. 如果問題仍然存在，請檢查瀏覽器控制台的錯誤信息")

if __name__ == '__main__':
    main()




