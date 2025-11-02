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
        
        // 保存原始值，確保 getActualValue 能正確返回
        // 使用 input.value 或 options.initialValue
        this._actualValue = options.initialValue !== undefined ? options.initialValue : this.input.value;
        if (this._actualValue) {
            this.input.value = this._actualValue;
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 保存原有的 _actualValue，避免在添加事件監聽器時被清空
        const existingValue = this._actualValue;
        
        // 輸入事件
        this.input.addEventListener('input', (e) => this.handleInput(e));
        
        // 失去焦點事件
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        // 鍵盤事件
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // 確保添加事件監聽器後值不會被清空
        if (existingValue) {
            this._actualValue = existingValue;
            this.input.value = existingValue;
        }
    }
    
    handleInput(e) {
        let rawValue = e.target.value;
        
        // 如果輸入框為空或值相同，不進行處理（避免重複觸發）
        if (!rawValue || rawValue === this._actualValue) {
            return;
        }
        
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
        
        // [修復] 限制小數位數，不把小數點當作一位數
        if (parts.length === 2) {
            // 有小數點的情況：限制小數部分最多為 maxDecimals 位
            const integerPart = parts[0];
            const decimalPart = parts[1];
            
            if (decimalPart.length > this.options.maxDecimals) {
                // 截斷超過的小數位數
                rawValue = integerPart + '.' + decimalPart.substring(0, this.options.maxDecimals);
            }
        }
        // 注意：如果沒有小數點，不應該自動添加小數點或限制整數部分

        // 保存實際值
        this._actualValue = rawValue;

        // 直接顯示清理後的值，不添加千位分隔符
        e.target.value = rawValue;
    }
    
    handleBlur(e) {
        // 確保 _actualValue 與 input.value 同步
        // 只有在值完全無效時才清空
        const currentValue = e.target.value.trim();
        if (currentValue === '' || currentValue === '-' || currentValue === '.') {
            e.target.value = '';
            this._actualValue = '';
        } else {
            // 保存實際值
            this._actualValue = currentValue;
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
    
    // 獲取實際數值（優先返回保存的值）
    getValue() {
        // 如果 _actualValue 存在，優先返回它
        if (this._actualValue !== undefined && this._actualValue !== null && this._actualValue !== '') {
            return this._actualValue;
        }
        // 否則返回 input.value
        return this.input.value || '';
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
    
    // 保存對 enhancedInput 的引用，方便其他代碼訪問
    inputElement._enhancedInput = enhancedInput;
    
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
