#!/usr/bin/env python3
"""
修復轉帳記錄顯示問題
"""

import re

def fix_transfer_display():
    """修復轉帳記錄顯示問題"""
    
    # 讀取app.py文件
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定義要替換的模式
    pattern = r'elif entry\.entry_type in \["TRANSFER"\]:\s*# 內部轉帳：從轉出帳戶 -> 轉入帳戶\s*if entry\.from_account and entry\.to_account:\s*payment_account = entry\.from_account\.name\s*deposit_account = entry\.to_account\.name\s*else:\s*# 向後兼容：從描述中提取帳戶名稱\s*if "從" in entry\.description and "轉入至" in entry\.description:\s*parts = entry\.description\.split\("從 "\)\[1\]\.split\(" 轉入至 "\)\s*if len\(parts\) == 2:\s*payment_account = parts\[0\]\s*deposit_account = parts\[1\]\s*else:\s*payment_account = "N/A"\s*deposit_account = "N/A"\s*else:\s*payment_account = "N/A"\s*deposit_account = "N/A"'
    
    replacement = '''elif entry.entry_type in ["TRANSFER"]:
                    # 內部轉帳：從轉出帳戶 -> 轉入帳戶
                    if entry.from_account and entry.to_account:
                        payment_account = entry.from_account.name
                        deposit_account = entry.to_account.name
                    else:
                        # 向後兼容：從描述中提取帳戶名稱
                        if "從" in entry.description and "轉入至" in entry.description:
                            parts = entry.description.split("從 ")[1].split(" 轉入至 ")
                            if len(parts) == 2:
                                payment_account = parts[0]
                                deposit_account = parts[1]
                            else:
                                payment_account = "N/A"
                                deposit_account = "N/A"
                        else:
                            payment_account = "N/A"
                            deposit_account = "N/A"
                elif entry.entry_type in ["TRANSFER_IN"]:
                    # 轉入記錄：從其他帳戶轉入
                    if entry.from_account:
                        payment_account = entry.from_account.name
                    else:
                        # 從描述中提取轉出帳戶名稱
                        if "從" in entry.description:
                            payment_account = entry.description.split("從")[1].split("轉入")[0].strip()
                        else:
                            payment_account = "其他帳戶"
                    deposit_account = entry.account.name if entry.account else "N/A"
                elif entry.entry_type in ["TRANSFER_OUT"]:
                    # 轉出記錄：轉出到其他帳戶
                    payment_account = entry.account.name if entry.account else "N/A"
                    if entry.to_account:
                        deposit_account = entry.to_account.name
                    else:
                        # 從描述中提取轉入帳戶名稱
                        if "轉出至" in entry.description:
                            deposit_account = entry.description.split("轉出至")[1].strip()
                        else:
                            deposit_account = "其他帳戶"'''
    
    # 執行替換
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # 寫回文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 轉帳記錄顯示修復完成")

if __name__ == "__main__":
    fix_transfer_display()
