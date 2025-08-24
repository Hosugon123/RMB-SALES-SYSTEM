// 增強的數字輸入處理腳本
// 解決 type="text" 與逗號格式化的兼容性問題

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
            value = value.replace(/[^\d.-]/g, '');
        } else {
            value = value.replace(/[^\d.]/g, '');
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

        // 修復小數點輸入問題 - 簡化邏輯
        if (value === '' || value === '.' || value === '-') {
            // 空值、單獨小數點或負號，直接顯示
            e.target.value = value;
        } else if (value.endsWith('.')) {
            // 以小數點結尾，不進行格式化，保持用戶輸入狀態
            e.target.value = value;
        } else if (value === '-.') {
            // 負號加小數點，不進行格式化
            e.target.value = value;
        } else {
            // 完整的數字，進行格式化
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                const maxDecimals = this.options.maxDecimals || 2;
                e.target.value = numValue.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: maxDecimals
                });
            } else {
                // 如果解析失敗，保持原始值（可能是正在輸入的狀態）
                e.target.value = value;
            }
        }
    }
    
    handleBlur(e) {
        // 改進失去焦點時的處理
        if (!e.target.value || e.target.value === '.' || e.target.value === '-') {
            e.target.value = '';
            this.originalValue = '';
        } else if (e.target.value.endsWith('.')) {
            // 如果以小數點結尾，移除小數點
            const cleanValue = e.target.value.slice(0, -1);
            if (cleanValue) {
                this.originalValue = cleanValue;
                e.target.value = cleanValue;
            } else {
                e.target.value = '';
                this.originalValue = '';
            }
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
        
        if (allowedKeys.includes(e.key) || /[\d.]/.test(e.key) || 
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

// 表單提交前的數字驗證和清理
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (!form.tagName || form.tagName !== 'FORM') return;
    
    // 查找所有數字輸入欄位
    const numberInputs = form.querySelectorAll('input[type="text"][pattern*="[0-9]"], input[type="text"][id*="amount"], input[type="text"][id*="rate"], input[type="text"][id*="balance"], input[type="text"][id*="rmb"]');
    
    numberInputs.forEach(input => {
        // 移除逗號，確保提交的是純數字
        if (input.value.includes(',')) {
            input.value = input.value.replace(/,/g, '');
        }
        
        // 驗證數字格式
        const value = input.value;
        if (value && !/^\d*\.?\d*$/.test(value)) {
            e.preventDefault();
            alert(`請輸入有效的數字格式: ${input.name || input.id}`);
            input.focus();
            return false;
        }
    });
});
