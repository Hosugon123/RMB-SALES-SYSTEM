// 簡化的數字輸入處理腳本
// 移除千位分隔符功能，只保留基本的數字驗證

class EnhancedNumberInput {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minDecimals: options.minDecimals || 0,
            maxDecimals: options.maxDecimals || 2,
            allowNegative: options.allowNegative || false,
            ...options
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 輸入事件
        this.input.addEventListener('input', (e) => this.handleInput(e));
        
        // 失去焦點事件
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        // 鍵盤事件
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
    }
    
    handleInput(e) {
        let rawValue = e.target.value;
        
        // 移除除了數字、小數點和負號以外的所有字元
        if (this.options.allowNegative) {
            rawValue = rawValue.replace(/[^0-9.-]/g, '');
        } else {
            rawValue = rawValue.replace(/[^0-9.]/g, '');
        }

        // 處理負號
        if (this.options.allowNegative && rawValue.startsWith('-')) {
            rawValue = '-' + rawValue.substring(1).replace(/-/g, '');
        }

        // 確保只有一個小數點
        const parts = rawValue.split('.');
        if (parts.length > 2) {
            rawValue = parts[0] + '.' + parts.slice(1).join('');
        }

        // 直接顯示清理後的值，不添加千位分隔符
        e.target.value = rawValue;
    }
    
    handleBlur(e) {
        // 失去焦點時的處理
        if (!e.target.value || e.target.value === '-' || e.target.value === '.') {
            e.target.value = '';
        }
    }
    
    handleKeydown(e) {
        // 允許的按鍵：數字、小數點、負號、退格、刪除、方向鍵、Tab、Enter
        const allowedKeys = [
            'Backspace', 'Delete', 'Tab', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'
        ];
        
        if (allowedKeys.includes(e.key) || /[\d.]/.test(e.key) || 
            (this.options.allowNegative && e.key === '-')) {
            return;
        }
        
        e.preventDefault();
    }
    
    // 獲取實際數值（直接返回輸入值）
    getValue() {
        return this.input.value;
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
    
    // 設置值（直接設置，不格式化）
    setValue(value) {
        this.input.value = value.toString();
    }
}

// 全局函數，用於向後兼容
function setupNumberInputFormatting(inputElement, options = {}) {
    if (!inputElement) return;
    
    // 創建簡化的數字輸入實例
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
    
    console.log('✅ 簡化的數字輸入處理已初始化（無千位分隔符）');
});

// 移除表單提交事件監聽器，避免衝突
// 表單提交時的數字處理由各頁面自行處理
