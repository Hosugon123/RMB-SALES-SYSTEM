#!/usr/bin/env python3
"""
修復app.py中的Unicode emoji字符，避免編碼錯誤
"""

import re

def fix_unicode_emojis():
    """修復Unicode emoji字符"""
    
    # 讀取文件
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定義替換映射
    replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        '🔍': '[DEBUG]',
        '📊': '[DATA]',
        '💰': '[MONEY]',
        '📈': '[UP]',
        '📉': '[DOWN]',
        '🎯': '[TARGET]',
        '🔧': '[FIX]',
        '🚀': '[START]',
        '⭐': '[STAR]',
        '💡': '[IDEA]',
        '🎨': '[STYLE]',
        '🔄': '[SYNC]',
        '🧪': '[TEST]'
    }
    
    # 執行替換
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # 寫回文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Unicode emoji字符修復完成")

if __name__ == "__main__":
    fix_unicode_emojis()
