document.addEventListener('DOMContentLoaded', function() {
    // Add new order item row
    document.getElementById('add-item').addEventListener('click', function() {
        const newRow = document.querySelector('.item-row').cloneNode(true);
        newRow.querySelector('.product-select').value = '';
        newRow.querySelector('.quantity').value = 1;
        newRow.querySelector('.price').value = '';
        document.getElementById('order-items').appendChild(newRow);
        addRowEventListeners(newRow);
    });

    // Add event listeners to initial row
    addRowEventListeners(document.querySelector('.item-row'));

    function addRowEventListeners(row) {
        const productSelect = row.querySelector('.product-select');
        const quantityInput = row.querySelector('.quantity');
        const priceInput = row.querySelector('.price');
        const removeBtn = row.querySelector('.remove-item');

        productSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const price = selectedOption.dataset.price || '0';
            priceInput.value = '$' + parseFloat(price).toFixed(2);
            calculateTotal();
        });

        quantityInput.addEventListener('change', function() {
            calculateTotal();
        });

        removeBtn.addEventListener('click', function() {
            if (document.querySelectorAll('.item-row').length > 1) {
                row.remove();
                calculateTotal();
            } else {
                alert('An order must have at least one item.');
            }
        });
    }

    function calculateTotal() {
        let total = 0;
        document.querySelectorAll('.item-row').forEach(row => {
            const productSelect = row.querySelector('.product-select');
            const quantityInput = row.querySelector('.quantity');
            
            if (productSelect.value && quantityInput.value) {
                const selectedOption = productSelect.options[productSelect.selectedIndex];
                const price = parseFloat(selectedOption.dataset.price || 0);
                const quantity = parseInt(quantityInput.value || 0);
                total += price * quantity;
            }
        });

        document.getElementById('order-total').textContent = total.toFixed(2);
    }
});