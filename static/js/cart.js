// static/js/cart.js
// ALChicken Shopping Cart

class ShoppingCart {
    constructor() {
        this.cart        = [];
        this.pending     = false;
        this.currentPage = this.detectPage();

        if (this.currentPage === 'confirmation') return;
        this.loadCartThenInit();
    }

    detectPage() {
        const path = window.location.pathname;
        if (path.includes('/cart'))               return 'cart';
        if (path.includes('/checkout'))           return 'checkout';
        if (path.includes('/products'))           return 'products';
        if (path === '/' || path === '/index')    return 'home';
        if (path.includes('/order-confirmation')) return 'confirmation';
        return 'other';
    }

   loadCartThenInit() {
    fetch('/api/cart', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ action: 'get' })
    })
    .then(r => r.json())
    .then(data => {
        this.cart = data.cart || [];
        this.normalizeCart();          // ← normalize BEFORE anything renders
        this.updateCartCount();
        switch (this.currentPage) {
            case 'cart':     this.initCartPage();     break;
            case 'products':
            case 'home':     this.initProductPages(); break;
            case 'checkout': this.initCheckoutPage(); break;
        }
    })
    .catch(err => console.error('Error loading cart:', err));
}

    // ── Page initialisers ─────────────────────────────────────────────────────

    initProductPages() {
        document.querySelectorAll('.add-to-cart').forEach(button => {
            const newBtn = button.cloneNode(true);
            button.parentNode.replaceChild(newBtn, button);
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (this.pending) return;
                const productId = newBtn.dataset.productId;
                let quantity    = 1;
                const qtyInput  = document.querySelector(`#quantity-${productId}`);
                if (qtyInput) quantity = parseInt(qtyInput.value) || 1;
                this.addToCart(productId, quantity);
            });
        });
    }

    initCartPage() {
        this.renderCartTable();
        const clearBtn = document.querySelector('.btn-clear-cart');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to clear your cart?')) this.clearCart();
            });
        }
    }

    initCheckoutPage() {
    this.normalizeCart(); // ✅ FIX: use class method
    this.updateCartCount();
    this.updateCheckoutTotals();
    

    document.querySelectorAll('input[name="delivery_option"]').forEach(radio => {
        radio.addEventListener('change', () => this.updateCheckoutTotals());
    });
}

    normalizeCart() {
    const map = {};
    this.cart.forEach(item => {
        const id = String(item.product_id);  // ← force string comparison
        if (!map[id]) {
            map[id] = { ...item };
        } else {
            map[id].quantity = Math.min(
                map[id].quantity + item.quantity,
                item.max_stock || map[id].max_stock
            );
        }
    });
    this.cart = Object.values(map);
}
    // ── Render cart table ─────────────────────────────────────────────────────

    renderCartTable() {
        const tbody = document.getElementById('cartItems');
        if (!tbody) return;

        if (this.cart.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="5" style="text-align:center;padding:40px;">
                    <i class="fas fa-shopping-cart" style="font-size:48px;color:#ccc;"></i>
                    <p style="margin:15px 0;">Your cart is empty</p>
                    <a href="/products" class="btn btn-primary">Browse Products</a>
                </td></tr>`;
            this.updateTotals({ subtotal: 0, tax: 0, delivery_fee: 0, total: 0 });
            return;
        }

        tbody.innerHTML = this.cart.map(item => `
            <tr data-product-id="${item.product_id}">
                <td class="product-info">
                    <img src="${item.image_url
                        ? `/static/images/products/${item.image_url}`
                        : '/static/images/chicken-placeholder.jpg'}"
                        alt="${this.escapeHtml(item.name)}" class="cart-product-image">
                    <span>${this.escapeHtml(item.name)}</span>
                </td>
                <td class="price">${this.formatPrice(item.price)}</td>
                <td class="quantity">
                    <div class="quantity-controls">
                        <button class="quantity-decrease" data-id="${item.product_id}">-</button>
                        <input type="number" class="cart-quantity" id="qty-${item.product_id}"
                               value="${item.quantity}" min="1" max="${item.max_stock}">
                        <button class="quantity-increase" data-id="${item.product_id}">+</button>
                        <button class="update-cart-btn" data-product-id="${item.product_id}">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </td>
                <td class="item-total" id="item-total-${item.product_id}">
                    ${this.formatPrice(item.price * item.quantity)}
                </td>
                <td>
                    <button class="remove-item-btn" data-product-id="${item.product_id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`).join('');

        this.bindCartEvents();
        this.recalculateTotals();
    }

    bindCartEvents() {
        document.querySelectorAll('.update-cart-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id  = btn.dataset.productId;
                const qty = parseInt(document.getElementById(`qty-${id}`).value);
                this.updateCartItem(id, qty);
            });
        });

        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', () => this.removeFromCart(btn.dataset.productId));
        });

        document.querySelectorAll('.quantity-decrease').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.pending) return;
                const input = document.getElementById(`qty-${btn.dataset.id}`);
                let val     = parseInt(input.value);
                if (val > 1) { input.value = val - 1; this.updateCartItem(btn.dataset.id, val - 1); }
            });
        });

        document.querySelectorAll('.quantity-increase').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.pending) return;
                const input = document.getElementById(`qty-${btn.dataset.id}`);
                const max   = parseInt(input.max);
                let val     = parseInt(input.value);
                if (val < max) { input.value = val + 1; this.updateCartItem(btn.dataset.id, val + 1); }
                else           { this.showNotification(`Only ${max} in stock`, 'error'); }
            });
        });

        const debounceTimers = {};
        document.querySelectorAll('.cart-quantity').forEach(input => {
            input.addEventListener('input', () => {
                const id = input.id.replace('qty-', '');
                clearTimeout(debounceTimers[id]);
                debounceTimers[id] = setTimeout(() => {
                    let val   = parseInt(input.value);
                    const max = parseInt(input.max);
                    if (isNaN(val) || val < 1) val = 1;
                    if (val > max) { val = max; this.showNotification(`Only ${max} in stock`, 'error'); }
                    input.value = val;
                    this.updateCartItem(id, val);
                }, 600);
            });
        });
    }

    // ── Cart actions ──────────────────────────────────────────────────────────

    addToCart(productId, quantity) {
        // Check stock locally BEFORE sending to server
        const existing = this.cart.find(i => i.product_id == productId);
        if (existing) {
            const canAdd = existing.max_stock - existing.quantity;
            if (canAdd <= 0) {
                this.showNotification(`You already have all ${existing.max_stock} in your cart`, 'error');
                return;
            }
            if (quantity > canAdd) {
                this.showNotification(`Only ${canAdd} more can be added`, 'error');
                quantity = canAdd;
            }
        }

        this.pending = true;

        fetch('/api/cart', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ action: 'add', product_id: productId, quantity })
        })
        .then(r => {
            // FIX: check HTTP status before parsing
            if (!r.ok) return r.json().then(d => { throw new Error(d.error || 'Server error'); });
            return r.json();
        })
        .then(data => {
            if (data.success) {
                if (existing) {
                    existing.quantity = Math.min(existing.quantity + quantity, existing.max_stock);
                    this.updateCartCount();
                    // FIX: show notification AFTER confirming success
                    this.showNotification('Added to cart!', 'success');
                    this.animateCartIcon();
                } else {
                    // New product — fetch once for full details
                    fetch('/api/cart', {
                        method:  'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body:    JSON.stringify({ action: 'get' })
                    })
                    .then(r => r.json())
                    .then(d => {
                        this.cart = d.cart || [];
                        this.updateCartCount();
                        this.showNotification('Added to cart!', 'success');
                        this.animateCartIcon();
                    });
                }
            } else {
                this.showNotification(data.error || 'Error adding to cart', 'error');
            }
        })
        .catch(err => {
            this.showNotification(err.message || 'Error adding to cart', 'error');
        })
        .finally(() => { this.pending = false; });
    }

    updateCartItem(productId, quantity) {
        const item = this.cart.find(i => i.product_id == productId);
        if (item && quantity > item.max_stock) {
            quantity = item.max_stock;
            const input = document.getElementById(`qty-${productId}`);
            if (input) input.value = quantity;
            this.showNotification(`Only ${item.max_stock} in stock`, 'error');
        }

        fetch('/api/cart', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ action: 'update', product_id: productId, quantity })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (quantity <= 0) {
                    this.cart = this.cart.filter(i => i.product_id != productId);
                    this.renderCartTable();
                } else if (item) {
                    item.quantity = quantity;
                    const cell = document.getElementById(`item-total-${productId}`);
                    if (cell) cell.textContent = this.formatPrice(item.price * quantity);
                    this.recalculateTotals();
                }
                this.updateCartCount();
            } else {
                this.showNotification(data.error || 'Error updating cart', 'error');
            }
        })
        .catch(() => this.showNotification('Error updating cart', 'error'));
    }

    removeFromCart(productId) {
        fetch('/api/cart', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ action: 'remove', product_id: productId })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                this.cart = this.cart.filter(i => i.product_id != productId);
                this.updateCartCount();
                this.renderCartTable();
                this.showNotification('Item removed', 'success');
            }
        })
        .catch(() => this.showNotification('Error removing item', 'error'));
    }

    clearCart() {
        fetch('/api/cart', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ action: 'clear' })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                this.cart = [];
                this.updateCartCount();
                this.renderCartTable();
                this.showNotification('Cart cleared', 'success');
            }
        })
        .catch(() => this.showNotification('Error clearing cart', 'error'));
    }

    // ── Totals ────────────────────────────────────────────────────────────────

    recalculateTotals() {
        const isDelivery = document.querySelector('input[name="delivery_option"]:checked')?.value === 'delivery';
        const subtotal   = this.cart.reduce((s, i) => s + i.price * i.quantity, 0);
        const tax        = subtotal * 0.15;
        const delivery   = isDelivery ? 500 : 0;
        this.updateTotals({ subtotal, tax, delivery_fee: delivery, total: subtotal + tax + delivery });
    }

    updateTotals(t) {
        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = this.formatPrice(v); };
        set('subtotal',    t.subtotal);
        set('tax',         t.tax);
        set('deliveryFee', t.delivery_fee);
        set('total',       t.total);
    }

    updateCheckoutTotals() {
        const isDelivery = document.querySelector('input[name="delivery_option"]:checked')?.value === 'delivery';
        const subtotal   = this.cart.reduce((s, i) => s + i.price * i.quantity, 0);
        const tax        = subtotal * 0.15;
        const delivery   = isDelivery ? 500 : 0;
        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = this.formatPrice(v); };
        set('checkout-subtotal', subtotal);
        set('checkout-tax',      tax);
        set('checkout-delivery', delivery);
        set('checkout-total',    subtotal + tax + delivery);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    updateCartCount() {
        const total = this.cart.reduce((s, i) => s + i.quantity, 0);
        document.querySelectorAll('#cartCount').forEach(el => el.textContent = total);
    }

    formatPrice(price) {
        return 'JMD ' + parseFloat(price).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    showNotification(message, type) {
        document.querySelectorAll('.notification').forEach(n => n.remove());
        const n = document.createElement('div');
        n.className   = `notification ${type}`;
        n.textContent = message;
        document.body.appendChild(n);
        setTimeout(() => {
            n.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => n.remove(), 300);
        }, 3000);
    }

    animateCartIcon() {
        const icon = document.querySelector('.cart-link i');
        if (icon) {
            icon.classList.add('bounce');
            setTimeout(() => icon.classList.remove('bounce'), 500);
        }
    }
}

let cartInstance = null;
document.addEventListener('DOMContentLoaded', () => { cartInstance = new ShoppingCart(); });
window.cart = () => cartInstance;

