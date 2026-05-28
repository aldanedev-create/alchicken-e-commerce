// static/js/customer_note.js
// Auto-saves customer note on the order confirmation page

(function () {
    const noteArea  = document.getElementById('customerNote');
    const noteSaved = document.getElementById('noteSaved');

    if (!noteArea || !noteSaved) return;

    // Order ID is stored on the textarea via data-order-id attribute
    // e.g. <textarea id="customerNote" data-order-id="{{ order.order_id }}">
    const orderId = noteArea.dataset.orderId;

    if (!orderId) {
        console.error('customer_note.js: missing data-order-id on #customerNote');
        return;
    }

    let timer;

    noteArea.addEventListener('input', () => {
        // FIX: plain property access - [noteSaved.style] was a broken hyperlink
        noteSaved.textContent  = 'Saving...';
        noteSaved.style.color  = 'var(--gray-color)';
        noteSaved.style.display = 'block';

        clearTimeout(timer);
        timer = setTimeout(saveNote, 1000);
    });

    function saveNote() {
        fetch(`/order/${orderId}/note`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ note: noteArea.value })
        })
        .then(r => {
            // FIX: check HTTP status before parsing JSON
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            if (data.success) {
                noteSaved.textContent  = '✓ Note saved';
                noteSaved.style.color  = 'var(--success-color)';
                setTimeout(() => { noteSaved.style.display = 'none'; }, 3000);
            } else {
                noteSaved.textContent = '✗ Could not save note';
                noteSaved.style.color = 'var(--danger-color)';
                console.error('Note save error:', data.error);
            }
        })
        .catch(err => {
            // FIX: plain property access
            noteSaved.textContent = '✗ Connection error';
            noteSaved.style.color = 'var(--danger-color)';
            console.error('Fetch error:', err);
        });
    }
})();