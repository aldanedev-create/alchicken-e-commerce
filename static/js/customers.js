// ALChicken - Admin Manage Customers JS

document.addEventListener('DOMContentLoaded', function () {

    // ── Search filter ─────────────────────────────────────────────────────────
    const searchInput = document.getElementById('searchCustomers');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            applyFilters();
        });
    }

    // ── Order filter ──────────────────────────────────────────────────────────
    const orderFilter = document.getElementById('orderFilter');
    if (orderFilter) {
        orderFilter.addEventListener('change', applyFilters);
    }

    function applyFilters() {
        const search = searchInput ? searchInput.value.toLowerCase() : '';
        const filter = orderFilter ? orderFilter.value : 'all';
        const rows = document.querySelectorAll('#customersTableBody tr');

        rows.forEach(row => {
            const name = row.querySelector('td:nth-child(2) strong');
            const email = row.querySelector('td:nth-child(2) small');
            const orderCount = parseInt(row.dataset.orderCount || '0', 10);

            const matchesSearch =
                !search ||
                (name && name.textContent.toLowerCase().includes(search)) ||
                (email && email.textContent.toLowerCase().includes(search));

            const matchesFilter =
                filter === 'all' ||
                (filter === 'has_orders' && orderCount > 0) ||
                (filter === 'no_orders' && orderCount === 0);

            row.style.display = matchesSearch && matchesFilter ? '' : 'none';
        });
    }

    // ── View customer modal ───────────────────────────────────────────────────
    const viewModal = document.getElementById('viewCustomerModal');

    window.viewCustomer = function (userId) {
        const row = document.querySelector(`#customersTableBody tr [onclick*="${userId}"]`).closest('tr');
        const name = row.querySelector('td:nth-child(2) strong').textContent;
        const email = row.querySelector('td:nth-child(2) small').textContent;
        const contact = row.querySelector('td:nth-child(3)').innerHTML;
        const orders = row.querySelector('td:nth-child(4)').textContent.trim();
        const spent = row.querySelector('td:nth-child(5)').textContent.trim();
        const joined = row.querySelector('td:nth-child(6)').textContent.trim();

        document.getElementById('customerDetails').innerHTML = `
            <div class="customer-detail-grid">
                <p><strong>Name:</strong> ${name}</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Contact:</strong> ${contact}</p>
                <p><strong>Orders:</strong> ${orders}</p>
                <p><strong>Total Spent:</strong> ${spent}</p>
                <p><strong>Joined:</strong> ${joined}</p>
            </div>`;
        viewModal.style.display = 'flex';
    };

    window.closeViewModal = function () {
        if (viewModal) viewModal.style.display = 'none';
    };

    // ── Delete customer modal ─────────────────────────────────────────────────
    const deleteModal = document.getElementById('deleteModal');
    const deleteForm = document.getElementById('deleteCustomerForm');

    window.deleteCustomer = function (userId, customerName) {
        document.getElementById('deleteCustomerName').textContent = customerName;
        deleteForm.action = `/admin/customers/delete/${userId}`;
        deleteModal.style.display = 'flex';
    };

    window.closeDeleteModal = function () {
        if (deleteModal) deleteModal.style.display = 'none';
    };

    // ── Close modals on outside click ─────────────────────────────────────────
    window.addEventListener('click', function (e) {
        if (e.target === viewModal) closeViewModal();
        if (e.target === deleteModal) closeDeleteModal();
    });
});
