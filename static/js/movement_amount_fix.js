// 專門修復 movementAmount 欄位的腳本
// 解決數字格式化問題

(function() {
    'use strict';
    
    console.log('🔧 movementAmount 修復腳本已載入');
    
    // 等待 DOM 載入完成
    function waitForElement(selector, callback) {
        if (document.querySelector(selector)) {
            callback();
        } else {
            setTimeout(() => waitForElement(selector, callback), 100);
        }
    }
    
    // 修復 movementAmount 欄位
    function fixMovementAmount() {
        const movementAmountInput = document.getElementById('movementAmount');
        if (!movementAmountInput) {
            console.log('❌ 找不到 movementAmount 欄位');
            return;
        }
        
        console.log('✅ 找到 movementAmount 欄位，開始修復');
        
        // 移除所有現有的事件監聽器
        const newInput = movementAmountInput.cloneNode(true);
        movementAmountInput.parentNode.replaceChild(newInput, movementAmountInput);
        
        // 重新獲取新的元素引用
        const fixedInput = document.getElementById('movementAmount');
        
        // 設置基本屬性
        fixedInput.type = 'text';
        fixedInput.pattern = '[0-9]*\\.?[0-9]*';
        fixedInput.className = 'form-control';
        fixedInput.required = true;
        
        // 自定義的數字格式化邏輯
        let originalValue = '';
        
        function formatNumber(value) {
            if (!value || value === '' || value === '-' || value === '.') {
                return value;
            }
            
            // 移除所有非數字和小數點的字元
            let cleanValue = value.replace(/[^0-9.]/g, '');
            
            // 確保只有一個小數點
            const parts = cleanValue.split('.');
            if (parts.length > 2) {
                cleanValue = parts[0] + '.' + parts.slice(1).join('');
            }
            
            // 分割整數和小數部分
            const integerPart = parts[0];
            const decimalPart = parts.length > 1 ? '.' + parts[1] : '';
            
            // 千分位格式化
            let formattedInteger = '';
            if (integerPart.length > 3) {
                for (let i = integerPart.length - 1, count = 0; i >= 0; i--, count++) {
                    if (count > 0 && count % 3 === 0) {
                        formattedInteger = ',' + formattedInteger;
                    }
                    formattedInteger = integerPart[i] + formattedInteger;
                }
            } else {
                formattedInteger = integerPart;
            }
            
            return formattedInteger + decimalPart;
        }
        
        // 輸入事件處理
        fixedInput.addEventListener('input', function(e) {
            const inputValue = e.target.value;
            console.log('🔍 輸入事件:', {
                inputValue: inputValue,
                originalValue: originalValue
            });
            
            // 如果輸入的是格式化後的值，不要重複格式化
            if (inputValue.includes(',') && originalValue && !originalValue.includes(',')) {
                return;
            }
            
            // 保存原始值
            originalValue = inputValue.replace(/,/g, '');
            
            // 格式化顯示
            const formatted = formatNumber(originalValue);
            if (formatted !== inputValue) {
                e.target.value = formatted;
            }
            
            console.log('🔧 格式化結果:', {
                original: originalValue,
                formatted: formatted
            });
        });
        
        // 聚焦事件處理
        fixedInput.addEventListener('focus', function(e) {
            if (originalValue) {
                e.target.value = originalValue;
            }
        });
        
        // 失去焦點事件處理
        fixedInput.addEventListener('blur', function(e) {
            if (e.target.value) {
                const formatted = formatNumber(e.target.value);
                e.target.value = formatted;
            }
        });
        
        // 獲取實際值的方法
        fixedInput.getActualValue = function() {
            return originalValue || this.value.replace(/,/g, '');
        };
        
        // 設置值的方法
        fixedInput.setValue = function(value) {
            originalValue = value.toString();
            this.value = formatNumber(value);
        };
        
        console.log('✅ movementAmount 欄位修復完成');
    }
    
    // 等待頁面載入完成後執行修復
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            waitForElement('#movementAmount', fixMovementAmount);
        });
    } else {
        waitForElement('#movementAmount', fixMovementAmount);
    }
    
    // 監聽模態框顯示事件
    document.addEventListener('show.bs.modal', function(e) {
        if (e.target.id === 'addMovementModal') {
            setTimeout(fixMovementAmount, 100);
        }
    });
    
    // 監聽模態框隱藏事件
    document.addEventListener('hidden.bs.modal', function(e) {
        if (e.target.id === 'addMovementModal') {
            const movementAmountInput = document.getElementById('movementAmount');
            if (movementAmountInput) {
                movementAmountInput.value = '';
            }
        }
    });
    
})();
