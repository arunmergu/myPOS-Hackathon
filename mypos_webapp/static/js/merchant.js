document.addEventListener('DOMContentLoaded', function() {
    // Filter quotations
    const filterSelect = document.getElementById('filter-status');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const status = this.value;
            const quotationRows = document.querySelectorAll('.quotation-row');
            
            quotationRows.forEach(row => {
                if (status === 'all' || row.dataset.status === status) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Calculate deposit amount - Enhanced version
    const amountInput = document.getElementById('amount');
    const depositPercentInput = document.getElementById('deposit-percent');
    const depositAmountInput = document.getElementById('deposit-amount');
    
    if (amountInput && depositPercentInput && depositAmountInput) {
        // More precise calculation function
        function calculateDeposit() {
            const totalAmount = parseFloat(amountInput.value) || 0;
            const percentage = parseFloat(depositPercentInput.value) || 0;
            
            // Calculate deposit - make sure to handle decimals properly
            const depositAmount = (totalAmount * percentage / 100).toFixed(2);
            depositAmountInput.value = depositAmount;
            
            // Update visual display as well if it exists
            const depositDisplayElement = document.getElementById('deposit-display');
            if (depositDisplayElement) {
                depositDisplayElement.textContent = `€${depositAmount}`;
            }
        }
        
        // Initialize on page load
        calculateDeposit();
        
        // Add event listeners to recalculate on change
        amountInput.addEventListener('input', calculateDeposit);
        depositPercentInput.addEventListener('input', calculateDeposit);
        
        // Add event listener for percentage presets if they exist
        const percentageButtons = document.querySelectorAll('.percentage-preset');
        if (percentageButtons.length > 0) {
            percentageButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Set the percentage input to the button's value
                    depositPercentInput.value = this.dataset.percentage;
                    
                    // Update active state on buttons
                    percentageButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Recalculate deposit
                    calculateDeposit();
                });
            });
        }
    }
});