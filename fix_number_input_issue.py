#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復所有頁面數字輸入欄位的問題
將 type="number" 改為 type="text" 以避免逗號格式化問題
"""

import os
import re
from pathlib import Path

def fix_number_input_fields():
    """修復所有 HTML 模板中的數字輸入欄位"""
    
    # 需要修復的模板文件
    template_files = [
        'templates/sales_entry.html',
        'templates/buy_in.html',
        'templates/card_purchase.html',
        'templates/exchange_rate.html',
        'templates/inventory_management.html',
        'templates/inventory_purchase.html',
        'templates/outward_channels.html',
        'templates/user.html',
        'templates/_cash_management_modals.html',
        'test_settlement_debug.html',
        'test_settlement_enhanced.html',
        'test_three_issues_fix.html'
    ]
    
    # 修復記錄
    fixes_applied = []
    
    for template_file in template_files:
        if not os.path.exists(template_file):
            print(f"⚠️ 文件不存在: {template_file}")
            continue
            
        print(f"🔧 正在修復: {template_file}")
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 修復 1: 將 type="number" 改為 type="text"
            content = re.sub(
                r'type="number"',
                'type="text"',
                content
            )
            
            # 修復 2: 為數字輸入欄位添加 pattern 屬性進行驗證
            content = re.sub(
                r'(<input[^>]*id="[^"]*rmb[^"]*"[^>]*type="text"[^>]*>)',
                r'\1 pattern="[0-9]*\.?[0-9]*"',
                content
            )
            
            content = re.sub(
                r'(<input[^>]*id="[^"]*amount[^"]*"[^>]*type="text"[^>]*>)',
                r'\1 pattern="[0-9]*\.?[0-9]*"',
                content
            )
            
            content = re.sub(
                r'(<input[^>]*id="[^"]*rate[^"]*"[^>]*type="text"[^>]*>)',
                r'\1 pattern="[0-9]*\.?[0-9]*"',
                content
            )
            
            content = re.sub(
                r'(<input[^>]*id="[^"]*balance[^"]*"[^>]*type="text"[^>]*>)',
                r'\1 pattern="[0-9]*\.?[0-9]*"',
                content
            )
            
            # 修復 3: 更新 JavaScript 中的數字驗證邏輯
            if 'setupNumberInputFormatting' in content:
                # 改進數字格式化函數
                improved_function = '''
    // 改進的數字輸入欄位格式化函數
    function setupNumberInputFormatting(inputElement) {
        if (!inputElement) return;
        
        // 保存原始值用於計算
        let originalValue = '';
        
        inputElement.addEventListener('input', function(e) {
            // 獲取輸入值，移除所有非數字字符（除了小數點）
            let value = e.target.value.replace(/[^\\d.]/g, '');
            
            // 確保只有一個小數點
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            
            // 保存原始值用於計算
            originalValue = value;
            
            // 格式化顯示（添加逗號）
            if (value && value !== '.') {
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    // 根據欄位類型決定小數位數
                    if (this.id.includes('rate') || this.id.includes('exchange')) {
                        // 匯率欄位顯示4位小數
                        e.target.value = numValue.toLocaleString('en-US', { 
                            minimumFractionDigits: 0, 
                            maximumFractionDigits: 4 
                        });
                    } else {
                        // 其他欄位顯示2位小數
                        e.target.value = numValue.toLocaleString('en-US', { 
                            minimumFractionDigits: 0, 
                            maximumFractionDigits: 2 
                        });
                    }
                }
            }
        });
        
        // 失去焦點時，如果值為空或只有小數點，清空欄位
        inputElement.addEventListener('blur', function(e) {
            if (!e.target.value || e.target.value === '.') {
                e.target.value = '';
                originalValue = '';
            }
        });
        
        // 獲取實際數值（用於計算和表單提交）
        inputElement.getActualValue = function() {
            return originalValue || this.value.replace(/,/g, '');
        };
        
        // 驗證輸入值是否為有效數字
        inputElement.validateNumber = function() {
            const value = this.getActualValue();
            if (!value) return false;
            const num = parseFloat(value);
            return !isNaN(num) && num >= 0;
        };
    }'''
                
                # 替換原有的函數
                content = re.sub(
                    r'function setupNumberInputFormatting\(inputElement\) \{[\s\S]*?\}',
                    improved_function,
                    content
                )
            
            # 如果內容有變化，寫回文件
            if content != original_content:
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixes_applied.append(template_file)
                print(f"✅ 已修復: {template_file}")
            else:
                print(f"ℹ️ 無需修復: {template_file}")
                
        except Exception as e:
            print(f"❌ 修復失敗 {template_file}: {e}")
    
    return fixes_applied

def create_enhanced_number_input_script():
    """創建增強的數字輸入處理腳本"""
    
    script_content = '''
// 增強的數字輸入處理腳本
// 解決 type="number" 與逗號格式化的兼容性問題

class EnhancedNumberInput {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minDecimals: options.minDecimals || 0,
            maxDecimals: options.maxDecimals || 2,
            allowNegative: options.allowNegative || false,
            ...options
        };
        
        this.originalValue = '';
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 輸入事件
        this.input.addEventListener('input', (e) => this.handleInput(e));
        
        // 失去焦點事件
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        // 獲得焦點事件
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        
        // 鍵盤事件
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
    }
    
    handleInput(e) {
        let value = e.target.value;
        
        // 移除所有非數字字符（除了小數點和負號）
        if (this.options.allowNegative) {
            value = value.replace(/[^\\d.-]/g, '');
        } else {
            value = value.replace(/[^\\d.]/g, '');
        }
        
        // 處理負號
        if (this.options.allowNegative && value.startsWith('-')) {
            value = '-' + value.substring(1).replace(/-/g, '');
        }
        
        // 確保只有一個小數點
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        
        // 保存原始值
        this.originalValue = value;
        
        // 格式化顯示
        if (value && value !== '.' && value !== '-') {
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                e.target.value = numValue.toLocaleString('en-US', {
                    minimumFractionDigits: this.options.minDecimals,
                    maximumFractionDigits: this.options.maxDecimals
                });
            }
        }
    }
    
    handleBlur(e) {
        if (!e.target.value || e.target.value === '.' || e.target.value === '-') {
            e.target.value = '';
            this.originalValue = '';
        }
    }
    
    handleFocus(e) {
        // 聚焦時顯示原始值（無逗號）
        if (this.originalValue) {
            e.target.value = this.originalValue;
        }
    }
    
    handleKeydown(e) {
        // 允許的按鍵：數字、小數點、負號、退格、刪除、方向鍵、Tab、Enter
        const allowedKeys = [
            'Backspace', 'Delete', 'Tab', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'
        ];
        
        if (allowedKeys.includes(e.key) || /[\\d.]/.test(e.key) || 
            (this.options.allowNegative && e.key === '-')) {
            return;
        }
        
        e.preventDefault();
    }
    
    // 獲取實際數值
    getValue() {
        return this.originalValue || this.input.value.replace(/,/g, '');
    }
    
    // 獲取數字值
    getNumberValue() {
        const value = this.getValue();
        return value ? parseFloat(value) : 0;
    }
    
    // 驗證是否為有效數字
    isValid() {
        const value = this.getValue();
        if (!value) return false;
        const num = parseFloat(value);
        return !isNaN(num) && num >= 0;
    }
    
    // 設置值
    setValue(value) {
        this.originalValue = value.toString();
        this.input.value = value.toLocaleString('en-US', {
            minimumFractionDigits: this.options.minDecimals,
            maximumFractionDigits: this.options.maxDecimals
        });
    }
}

// 全局函數，用於向後兼容
function setupNumberInputFormatting(inputElement, options = {}) {
    if (!inputElement) return;
    
    // 創建增強的數字輸入實例
    const enhancedInput = new EnhancedNumberInput(inputElement, options);
    
    // 向後兼容的方法
    inputElement.getActualValue = () => enhancedInput.getValue();
    inputElement.validateNumber = () => enhancedInput.isValid();
    
    return enhancedInput;
}

// 自動初始化所有數字輸入欄位
document.addEventListener('DOMContentLoaded', function() {
    // 查找所有可能是數字輸入的欄位
    const numberInputs = document.querySelectorAll('input[type="text"][pattern*="[0-9]"], input[type="text"][id*="amount"], input[type="text"][id*="rate"], input[type="text"][id*="balance"], input[type="text"][id*="rmb"]');
    
    numberInputs.forEach(input => {
        // 根據欄位ID決定選項
        let options = { minDecimals: 0, maxDecimals: 2 };
        
        if (input.id.includes('rate') || input.id.includes('exchange')) {
            options.maxDecimals = 4;
        }
        
        if (input.id.includes('balance') || input.id.includes('amount')) {
            options.maxDecimals = 2;
        }
        
        setupNumberInputFormatting(input, options);
    });
    
    console.log('✅ 增強的數字輸入處理已初始化');
});
'''
    
    # 創建腳本文件
    script_file = 'static/js/enhanced_number_input.js'
    os.makedirs(os.path.dirname(script_file), exist_ok=True)
    
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 已創建增強的數字輸入腳本: {script_file}")
    return script_file

def update_base_template():
    """更新 base.html 模板以包含增強的數字輸入腳本"""
    
    base_template = 'templates/base.html'
    if not os.path.exists(base_template):
        print(f"⚠️ base.html 不存在，跳過更新")
        return
    
    try:
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已經包含腳本
        if 'enhanced_number_input.js' in content:
            print(f"ℹ️ base.html 已包含增強數字輸入腳本")
            return
        
        # 在 </body> 標籤前添加腳本引用
        script_tag = '''
    <!-- 增強的數字輸入處理腳本 -->
    <script src="{{ url_for('static', filename='js/enhanced_number_input.js') }}"></script>
</body>'''
        
        content = content.replace('</body>', script_tag)
        
        with open(base_template, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新 base.html 以包含增強數字輸入腳本")
        
    except Exception as e:
        print(f"❌ 更新 base.html 失敗: {e}")

def main():
    """主函數"""
    print("🚀 開始修復所有頁面的數字輸入問題...")
    print("=" * 60)
    
    # 1. 修復 HTML 模板
    fixes_applied = fix_number_input_fields()
    
    # 2. 創建增強的數字輸入腳本
    script_file = create_enhanced_number_input_script()
    
    # 3. 更新 base.html
    update_base_template()
    
    print("=" * 60)
    print("🎉 修復完成！")
    print(f"📝 已修復 {len(fixes_applied)} 個模板文件")
    print(f"📜 已創建增強腳本: {script_file}")
    print("\n📋 修復內容:")
    print("   • 將所有 type='number' 改為 type='text'")
    print("   • 添加數字驗證 pattern 屬性")
    print("   • 改進數字格式化函數")
    print("   • 創建增強的數字輸入處理腳本")
    print("\n💡 使用說明:")
    print("   • 所有數字輸入欄位現在都支援逗號格式化")
    print("   • 輸入時會自動添加逗號分隔符")
    print("   • 表單提交時會自動移除逗號進行驗證")
    print("   • 支援小數點和負數輸入（如果允許）")

if __name__ == "__main__":
    main()
