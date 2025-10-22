#!/usr/bin/env python3
"""
部署修復到線上環境
"""

import subprocess
import sys
import os

def deploy_fix():
    """部署修復到線上環境"""
    print("部署修復到線上環境...")
    
    try:
        # 檢查git狀態
        print("1. 檢查git狀態...")
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.stdout.strip():
            print("   有未提交的變更:")
            print(result.stdout)
        else:
            print("   工作目錄乾淨")
        
        # 添加所有變更
        print("2. 添加變更到git...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        # 提交變更
        print("3. 提交變更...")
        subprocess.run(['git', 'commit', '-m', '修復轉帳記錄顯示問題 - 完整修復版本'], check=True)
        
        # 推送到遠端
        print("4. 推送到遠端...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        
        print("✅ 部署完成！")
        print("請等待Render自動部署完成（通常需要2-3分鐘）")
        print("然後可以訪問: https://rmb-sales-system-test1.onrender.com/admin/cash_management")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 部署失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 部署失敗: {e}")
        return False

def main():
    """主函數"""
    print("部署修復到線上環境")
    print("=" * 50)
    
    if deploy_fix():
        print("\n部署成功！")
    else:
        print("\n部署失敗！")

if __name__ == "__main__":
    main()
