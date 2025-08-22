import sqlite3
import os
import shutil
from datetime import datetime
import json

def backup_local_database():
    """備份本地資料庫"""
    
    # 資料庫路徑
    db_path = 'instance/sales_system_v4.db'
    backup_dir = 'database_backups'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return None
    
    try:
        # 創建備份目錄
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 生成備份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'sales_system_v4_backup_{timestamp}.db')
        
        # 複製資料庫文件
        shutil.copy2(db_path, backup_file)
        
        print(f"✅ 資料庫備份成功: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"❌ 資料庫備份失敗: {e}")
        return None

def export_database_schema():
    """導出資料庫結構"""
    
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有表的結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema[table_name] = []
            for col in columns:
                schema[table_name].append({
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                })
        
        conn.close()
        
        # 保存結構到文件
        schema_file = 'database_schema.json'
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 資料庫結構導出成功: {schema_file}")
        return schema_file
        
    except Exception as e:
        print(f"❌ 資料庫結構導出失敗: {e}")
        return None

def export_critical_data():
    """導出關鍵數據"""
    
    db_path = 'instance/sales_system_v4.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 導出關鍵表的數據
        critical_tables = [
            'holders',
            'cash_accounts', 
            'purchase_records',
            'fifo_inventory',
            'customers',
            'sales_records',
            'fifo_sales_allocations',
            'ledger_entries'
        ]
        
        data_export = {}
        
        for table_name in critical_tables:
            try:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # 獲取列名
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # 轉換為字典格式
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        value = row[i]
                        # 處理日期類型
                        if isinstance(value, str) and 'T' in str(value):
                            try:
                                # 嘗試解析ISO格式日期
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                value = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                        row_dict[col_name] = value
                    table_data.append(row_dict)
                
                data_export[table_name] = {
                    'columns': columns,
                    'data': table_data,
                    'count': len(table_data)
                }
                
                print(f"  ✅ {table_name}: {len(table_data)} 筆記錄")
                
            except Exception as table_error:
                print(f"  ⚠️  {table_name}: 導出失敗 - {table_error}")
                data_export[table_name] = {'error': str(table_error)}
        
        conn.close()
        
        # 保存數據到文件
        data_file = 'database_data_export.json'
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data_export, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 關鍵數據導出成功: {data_file}")
        return data_file
        
    except Exception as e:
        print(f"❌ 關鍵數據導出失敗: {e}")
        return None

def create_render_sync_instructions():
    """創建Render同步說明文件"""
    
    instructions = """# Render 資料庫同步說明

## 🚨 緊急情況：資料庫不一致

本地資料庫狀態正常，但Render上的資料庫數據不正確。

## 📋 同步步驟

### 1. 備份當前Render資料庫
```bash
# 在Render控制台中備份當前資料庫
# 或使用Render的備份功能
```

### 2. 上傳本地資料庫文件
將以下文件上傳到Render：
- `sales_system_v4_backup_YYYYMMDD_HHMMSS.db` (完整資料庫備份)
- `database_schema.json` (資料庫結構)
- `database_data_export.json` (關鍵數據)

### 3. 恢復資料庫
```bash
# 方法1：直接替換資料庫文件
cp sales_system_v4_backup_YYYYMMDD_HHMMSS.db /path/to/render/database/

# 方法2：使用導出的數據重新構建
python restore_database.py
```

### 4. 驗證同步結果
- 檢查RMB帳戶餘額
- 檢查FIFO庫存狀態
- 確認數據一致性

## 🔍 問題分析

### 本地資料庫狀態
- RMB帳戶總餘額：[待檢查]
- FIFO庫存總RMB：[待檢查]
- 數據一致性：✅ 一致

### Render資料庫問題
- 刪除售出後款項沒有正確回到庫存和帳戶
- 可能原因：資料庫被意外清空或重置

## 🛡️ 預防措施

1. **設置資料庫保護機制**
2. **定期備份資料庫**
3. **檢查是否有自動執行的危險腳本**
4. **監控Render服務重啟事件**

## 📞 聯繫信息

如有問題，請檢查：
1. Render服務日誌
2. 資料庫連接狀態
3. 自動執行腳本
"""
    
    try:
        with open('RENDER_SYNC_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("✅ Render同步說明文件創建成功: RENDER_SYNC_INSTRUCTIONS.md")
        return True
        
    except Exception as e:
        print(f"❌ 創建說明文件失敗: {e}")
        return False

def main():
    """主函數：執行完整的資料庫同步準備"""
    
    print("🚀 開始準備資料庫同步到Render...")
    print("=" * 60)
    
    # 1. 備份本地資料庫
    print("\n📦 步驟1: 備份本地資料庫")
    backup_file = backup_local_database()
    
    # 2. 導出資料庫結構
    print("\n🏗️ 步驟2: 導出資料庫結構")
    schema_file = export_database_schema()
    
    # 3. 導出關鍵數據
    print("\n💾 步驟3: 導出關鍵數據")
    data_file = export_critical_data()
    
    # 4. 創建同步說明
    print("\n📋 步驟4: 創建同步說明")
    create_render_sync_instructions()
    
    print("\n" + "=" * 60)
    print("🎯 資料庫同步準備完成！")
    print("\n📁 生成的文件：")
    if backup_file:
        print(f"  - 資料庫備份: {backup_file}")
    if schema_file:
        print(f"  - 資料庫結構: {schema_file}")
    if data_file:
        print(f"  - 關鍵數據: {data_file}")
    print("  - 同步說明: RENDER_SYNC_INSTRUCTIONS.md")
    
    print("\n🚀 下一步：")
    print("1. 將備份文件上傳到Render")
    print("2. 按照說明文件執行同步")
    print("3. 驗證同步結果")

if __name__ == "__main__":
    main()
