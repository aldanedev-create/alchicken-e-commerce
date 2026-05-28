// Status filter
    document.getElementById('statusFilter').addEventListener('change', function() {
        const filter = this.value;
        const rows = document.querySelectorAll('#ordersTableBody tr');
        
        rows.forEach(row => {
            const status = row.dataset.status;
            if (filter === 'all' || status === filter) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
    
    // Search orders
    document.getElementById('searchOrders').addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('#ordersTableBody tr');
        
        rows.forEach(row => {
            const orderId = row.dataset.orderId;
            const customer = row.querySelector('td:nth-child(2) strong').textContent.toLowerCase();
            
            if (orderId.includes(searchTerm) || customer.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
    
// Safe date parser (handles multiple formats)
function parseDate(dateStr) {
    let d = new Date(dateStr);
    if (!isNaN(d)) return d;

    // Handle DD/MM/YYYY format
    const parts = dateStr.split('/');
    if (parts.length === 3) {
        return new Date(parts[2], parts[1] - 1, parts[0]);
    }

    return null;
}

// Date filter
document.getElementById('dateFilter').addEventListener('change', function() {
    const filter = this.value;
    const rows = document.querySelectorAll('#ordersTableBody tr');

    const now = new Date();

    rows.forEach(row => {
        const orderDate = parseDate(row.dataset.date);
        if (!orderDate) return;

        let show = false;

        if (filter === 'all') {
            show = true;
        }

        else if (filter === 'today') {
            const todayStr = now.toISOString().split('T')[0];
            const orderStr = orderDate.toISOString().split('T')[0];
            show = (todayStr === orderStr);
        }

        else if (filter === 'week') {
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);

            show = orderDate >= weekAgo && orderDate <= now;
        }

        else if (filter === 'month') {
            const monthAgo = new Date();
            monthAgo.setMonth(monthAgo.getMonth() - 1);

            show = orderDate >= monthAgo && orderDate <= now;
        }

        row.style.display = show ? '' : 'none';
    });
});