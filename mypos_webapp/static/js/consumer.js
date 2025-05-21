document.addEventListener('DOMContentLoaded', function() {
    // Filter quotations
    const filterSelect = document.getElementById('filter-status');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const status = this.value;
            const quotationCards = document.querySelectorAll('.quotation-card');
            
            quotationCards.forEach(card => {
                if (status === 'all' || card.dataset.status === status) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});