// static/js/order-details.js
// Admin Order Details - auto-saves note on typing

document.addEventListener('DOMContentLoaded', function () {

    const noteArea  = document.getElementById('customerNote');
    const orderId   = document.getElementById('orderId');
    const noteSaved = document.getElementById('noteSaved');

    // ── Auto-save admin note ──────────────────────────────────────────────────
    if (noteArea && orderId) {
        let autoSaveTimer;

        noteArea.addEventListener('input', () => {
            noteSaved.textContent   = 'Saving...';
            noteSaved.style.color   = 'var(--gray-color)';
            noteSaved.style.display = 'inline';

            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(() => saveAdminNote(orderId.value), 1000);
        });
    }

    function saveAdminNote(id) {
        const note  = document.getElementById('customerNote').value;
        const saved = document.getElementById('noteSaved');

        fetch(`/admin/orders/${id}/note`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note: note })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                saved.textContent = '✓ Saved';
                saved.style.color = 'var(--success-color)';
                setTimeout(() => { saved.style.display = 'none'; }, 3000);
            } else {
                saved.textContent = '✗ Error saving';
                saved.style.color = 'var(--danger-color)';
                console.error('Save error:', data.error);
            }
        })
        .catch(err => {
            saved.textContent = '✗ Connection error';
            saved.style.color = 'var(--danger-color)';
            console.error('Fetch error:', err);
        });
    }

    // Keep manual save button working too
    window.saveNote = function () {
        if (orderId) saveAdminNote(orderId.value);
    };

    // ── Mark as delivered ─────────────────────────────────────────────────────
    window.markAsDelivered = function () {
        if (confirm('Mark this order as delivered?')) {
            document.getElementById('order_status').value = 'completed';
            document.querySelector('.status-form').submit();
        }
    };

    // ── Mark as picked up ─────────────────────────────────────────────────────
    window.markAsPickedUp = function () {
        if (confirm('Mark this order as picked up?')) {
            document.getElementById('order_status').value = 'completed';
            document.querySelector('.status-form').submit();
        }
    };

    window.printOrder = function () { window.print(); };
});