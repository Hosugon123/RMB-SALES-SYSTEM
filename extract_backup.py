#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解壓備份檔案腳本
"""

import gzip
import tarfile
import os

backup_file = '2025-11-01T16_53Z.dir.tar.gz'
extract_to = 'backup_temp'

print(f"解壓 {backup_file}...")

try:
    # 創建目標目錄
    os.makedirs(extract_to, exist_ok=True)
    
    # 解壓 tar.gz
    with gzip.open(backup_file, 'rb') as f:
        with tarfile.open(fileobj=f) as tar:
            # 獲取所有成員
            members = tar.getmembers()
            print(f"找到 {len(members)} 個文件/目錄")
            
            # 列出內容
            for member in members:
                print(f"  {member.name} ({member.size} bytes)")
            
            # 解壓所有文件（跳過有問題的路徑）
            extracted = 0
            for member in members:
                try:
                    # 清理路徑，移除冒號等非法字符
                    safe_name = member.name.replace(':', '_')
                    if safe_name != member.name:
                        print(f"  重新命名: {member.name} -> {safe_name}")
                        member.name = safe_name
                    
                    tar.extract(member, extract_to)
                    extracted += 1
                except Exception as e:
                    print(f"  跳過 {member.name}: {e}")
            
            print(f"成功解壓 {extracted} 個文件")
            
except Exception as e:
    print(f"解壓失敗: {e}")
    import traceback
    traceback.print_exc()


