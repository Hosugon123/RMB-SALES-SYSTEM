#!/usr/bin/env python3
"""
簡單修復轉帳記錄顯示問題
"""

def fix_transfer_display():
    """修復轉帳記錄顯示問題"""
    
    # 讀取app.py文件
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到需要修復的位置
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 檢查是否是TRANSFER處理的開始
        if 'elif entry.entry_type in ["TRANSFER"]:' in line:
            # 找到這個區塊的結束位置
            j = i
            while j < len(lines) and not lines[j].strip().startswith('elif ') and not lines[j].strip().startswith('else:') and not lines[j].strip().startswith('if '):
                j += 1
            
            # 添加TRANSFER_IN和TRANSFER_OUT的處理
            new_lines.append(line)
            
            # 添加原有的TRANSFER處理邏輯
            for k in range(i+1, j):
                new_lines.append(lines[k])
            
            # 添加TRANSFER_IN處理
            new_lines.append('                elif entry.entry_type in ["TRANSFER_IN"]:\n')
            new_lines.append('                    # 轉入記錄：從其他帳戶轉入\n')
            new_lines.append('                    if entry.from_account:\n')
            new_lines.append('                        payment_account = entry.from_account.name\n')
            new_lines.append('                    else:\n')
            new_lines.append('                        # 從描述中提取轉出帳戶名稱\n')
            new_lines.append('                        if "從" in entry.description:\n')
            new_lines.append('                            payment_account = entry.description.split("從")[1].split("轉入")[0].strip()\n')
            new_lines.append('                        else:\n')
            new_lines.append('                            payment_account = "其他帳戶"\n')
            new_lines.append('                    deposit_account = entry.account.name if entry.account else "N/A"\n')
            
            # 添加TRANSFER_OUT處理
            new_lines.append('                elif entry.entry_type in ["TRANSFER_OUT"]:\n')
            new_lines.append('                    # 轉出記錄：轉出到其他帳戶\n')
            new_lines.append('                    payment_account = entry.account.name if entry.account else "N/A"\n')
            new_lines.append('                    if entry.to_account:\n')
            new_lines.append('                        deposit_account = entry.to_account.name\n')
            new_lines.append('                    else:\n')
            new_lines.append('                        # 從描述中提取轉入帳戶名稱\n')
            new_lines.append('                        if "轉出至" in entry.description:\n')
            new_lines.append('                            deposit_account = entry.description.split("轉出至")[1].strip()\n')
            new_lines.append('                        else:\n')
            new_lines.append('                            deposit_account = "其他帳戶"\n')
            
            i = j
        else:
            new_lines.append(line)
            i += 1
    
    # 寫回文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ 轉帳記錄顯示修復完成")

if __name__ == "__main__":
    fix_transfer_display()
