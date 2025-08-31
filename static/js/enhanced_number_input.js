// 增強的數字輸入處理腳本
// 解決 type="text" 與逗號格式化的兼容性問題，支援小數點輸入

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

        // 保存原始值
        this.originalValue = rawValue;

        // 如果原始值是空字串、負號或單獨小數點，直接顯示
        if (rawValue === '' || rawValue === '-' || rawValue === '.') {
            e.target.value = rawValue;
            return;
        }

        // 檢查是否正在輸入小數點（用戶剛輸入小數點）
        // 只有在用戶剛輸入小數點且沒有小數部分時才跳過格式化
        const isAddingDecimal = rawValue.endsWith('.') && parts.length === 2 && parts[1] === '';
        
        // 如果正在輸入小數點，保持原樣不進行格式化
        if (isAddingDecimal) {
            e.target.value = rawValue;
            return;
        }

        // 分割整數部分與小數部分
        let integerPart = parts[0];
        let decimalPart = parts.length > 1 ? '.' + parts[1] : '';

        // 修復：使用更安全的千分位格式化方法
        let formattedInteger = '';
        if (integerPart.length > 3) {
            // 從右到左每三位插入逗號
            for (let i = integerPart.length - 1, count = 0; i >= 0; i--, count++) {
                if (count > 0 && count % 3 === 0) {
                    formattedInteger = ',' + formattedInteger;
                }
                formattedInteger = integerPart[i] + formattedInteger;
            }
        } else {
            formattedInteger = integerPart;
        }

        // 將格式化後的整數和小數部分組合起來，並更新回輸入框
        e.target.value = formattedInteger + decimalPart;
    }
    
    handleBlur(e) {
        // 失去焦點時的處理
        if (!e.target.value || e.target.value === '-' || e.target.value === '.') {
            e.target.value = '';
            this.originalValue = '';
        } else if (e.target.value.endsWith('.')) {
            // 如果以小數點結尾，保持原樣，不自動移除
            // 這樣用戶可以輸入如 "4." 然後繼續輸入小數部分
            this.originalValue = e.target.value;
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
    
    // 獲取實際數值（移除逗號）
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
        
        // 格式化顯示值
        if (value === 0 || value === '0') {
            this.input.value = '0';
        } else {
            // 分割整數部分與小數部分
            const parts = value.toString().split('.');
            let integerPart = parts[0];
            let decimalPart = parts.length > 1 ? '.' + parts[1] : '';

            // 修復：使用更安全的千分位格式化方法
            let formattedInteger = '';
            if (integerPart.length > 3) {
                // 從右到左每三位插入逗號
                for (let i = integerPart.length - 1, count = 0; i >= 0; i--, count++) {
                    if (count > 0 && count % 3 === 0) {
                        formattedInteger = ',' + formattedInteger;
                    }
                    formattedInteger = integerPart[i] + formattedInteger;
                }
            } else {
                formattedInteger = integerPart;
            }

            // 組合格式化後的值
            this.input.value = formattedInteger + decimalPart;
        }
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
