document.addEventListener('DOMContentLoaded', function () {

    // ── Search ────────────────────────────────────────────────────────────────
    document.getElementById('searchProducts').addEventListener('keyup', function () {
        const searchTerm = this.value.toLowerCase();
        document.querySelectorAll('#productsTableBody tr').forEach(row => {
            const nameEl = row.querySelector('td:nth-child(3) strong');
            if (!nameEl) return;
            row.style.display = nameEl.textContent.toLowerCase().includes(searchTerm) ? '' : 'none';
        });
    });

    // ── Stock filter ──────────────────────────────────────────────────────────
    document.getElementById('stockFilter').addEventListener('change', function () {
        const filter = this.value;
        document.querySelectorAll('#productsTableBody tr').forEach(row => {
            const stock = parseInt(row.dataset.stock);
            let show = false;
            if (filter === 'all')                          show = true;
            else if (filter === 'low' && stock < 10 && stock > 0) show = true;
            else if (filter === 'out' && stock === 0)      show = true;
            else if (filter === 'in'  && stock > 0)        show = true;
            row.style.display = show ? '' : 'none';
        });
    });

    // ── Delete modal ──────────────────────────────────────────────────────────
    const deleteModal = document.getElementById('deleteModal');
    const deleteForm  = document.getElementById('deleteForm');

    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function () {
            const productId   = this.dataset.productId;
            const productName = this.dataset.productName;
            document.getElementById('deleteProductName').textContent = productName;
            // FIX 2: set the correct action URL before showing modal
            deleteForm.action = `/admin/products/delete/${productId}`;
            deleteModal.style.display = 'flex';
        });
    });

    document.getElementById('closeDeleteModal').addEventListener('click', () => {
        deleteModal.style.display = 'none';
    });
    document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
        deleteModal.style.display = 'none';
    });

    // ── Stock modal ───────────────────────────────────────────────────────────
    const stockModal = document.getElementById('stockModal');
    const stockForm  = document.getElementById('stockForm');

    document.querySelectorAll('.btn-stock').forEach(btn => {
        btn.addEventListener('click', function () {
            const productId    = this.dataset.productId;
            const currentStock = this.dataset.currentStock;
            // FIX 3: set the correct action URL before showing modal
            stockForm.action = `/admin/products/update-stock/${productId}`;
            // Pre-fill with current stock so admin knows what it is now
            document.getElementById('stockQuantity').value = currentStock;
            stockModal.style.display = 'flex';
        });
    });

    document.getElementById('closeStockModal').addEventListener('click', () => {
        stockModal.style.display = 'none';
    });
    document.getElementById('cancelStockBtn').addEventListener('click', () => {
        stockModal.style.display = 'none';
    });

    // ── Close on outside click ────────────────────────────────────────────────
    window.addEventListener('click', function (e) {
        if (e.target === deleteModal) deleteModal.style.display = 'none';
        if (e.target === stockModal)  stockModal.style.display  = 'none';
    });
});


