// ALChicken Main JavaScript
// Handles UI interactions, form validation, and mobile menu

document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize delivery option toggles
    initDeliveryOptions();
    
    // Initialize file upload validation
    initFileUpload();
    
    // Auto-dismiss flash messages
    initFlashMessages();
    
    // Initialize price formatting
    initPriceFormatting();
});

// Mobile Menu Toggle
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
}

// Form Validation
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const errors = [];
    
    // Validate email fields
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !validateEmail(field.value)) {
            errors.push('Please enter a valid email address');
            showFieldError(field, 'Invalid email format');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Validate phone fields (Jamaica format)
    const phoneFields = form.querySelectorAll('input[data-type="phone"], input[name="phone"], input[name="contact_number"]');
    phoneFields.forEach(field => {
        if (field.value && !validateJamaicaPhone(field.value)) {
            errors.push('Please enter a valid Jamaica phone number (876-XXX-XXXX)');
            showFieldError(field, 'Use format: 876-123-4567');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Validate required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value || field.value.trim() === '') {
            errors.push(`${field.name || field.id || 'Field'} is required`);
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Validate password match
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        errors.push('Passwords do not match');
        showFieldError(confirmPassword, 'Passwords do not match');
        isValid = false;
    }
    
    // Validate password length
    if (password && password.value && password.value.length < 6) {
        errors.push('Password must be at least 6 characters');
        showFieldError(password, 'Minimum 6 characters');
        isValid = false;
    }
    
    // Show all errors
    if (!isValid && errors.length > 0) {
        showFormErrors(form, errors);
    } else {
        clearFormErrors(form);
    }
    
    return isValid;
}

function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

function validateJamaicaPhone(phone) {
    // Remove all non-digit characters
    const digits = phone.replace(/\D/g, '');
    // Jamaica numbers: 876 or 658 followed by 7 digits
    return /^(876|658)\d{7}$/.test(digits);
}

function showFieldError(field, message) {
    field.classList.add('error');
    
    let errorSpan = field.parentElement.querySelector('.field-error');
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'field-error';
        field.parentElement.appendChild(errorSpan);
    }
    errorSpan.textContent = message;
    errorSpan.style.color = 'var(--danger-color)';
    errorSpan.style.fontSize = '12px';
    errorSpan.style.marginTop = '5px';
    errorSpan.style.display = 'block';
}

function clearFieldError(field) {
    field.classList.remove('error');
    
    const errorSpan = field.parentElement.querySelector('.field-error');
    if (errorSpan) {
        errorSpan.remove();
    }
}

function showFormErrors(form, errors) {
    let errorContainer = form.querySelector('.form-errors');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.className = 'form-errors';
        form.prepend(errorContainer);
    }
    
    errorContainer.innerHTML = `
        <div class="alert alert-danger">
            <ul>
                ${errors.map(e => `<li>${e}</li>`).join('')}
            </ul>
        </div>
    `;
}

function clearFormErrors(form) {
    const errorContainer = form.querySelector('.form-errors');
    if (errorContainer) {
        errorContainer.remove();
    }
}

// Delivery Options Toggle
function initDeliveryOptions() {
    const deliveryRadios = document.querySelectorAll('input[name="delivery_option"]');
    const deliveryAddress = document.getElementById('deliveryAddress');
    const deliveryFeeRow = document.getElementById('deliveryFeeRow');
    
    if (deliveryRadios.length > 0) {
        deliveryRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'delivery') {
                    if (deliveryAddress) {
                        deliveryAddress.style.display = 'block';
                        const addressField = document.getElementById('delivery_address');
                        if (addressField) addressField.required = true;
                    }
                    if (deliveryFeeRow) {
                        deliveryFeeRow.style.display = 'flex';
                    }
                } else {
                    if (deliveryAddress) {
                        deliveryAddress.style.display = 'none';
                        const addressField = document.getElementById('delivery_address');
                        if (addressField) addressField.required = false;
                    }
                    if (deliveryFeeRow) {
                        deliveryFeeRow.style.display = 'flex';
                    }
                }
            });
        });
    }
}

// File Upload Validation
function initFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                validateFile(file, this);
            }
        });
    });
}

function validateFile(file, input) {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    if (!allowedTypes.includes(file.type)) {
        showFileError(input, 'Invalid file type. Allowed: JPG, PNG, GIF, PDF,ZIP');
        return false;
    }
    
    if (file.size > maxSize) {
        showFileError(input, `File too large. Maximum ${maxSize / 1024 / 1024}MB`);
        return false;
    }
    
    clearFileError(input);
    
    // Show preview for images
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            let preview = input.parentElement.querySelector('.image-preview');
            if (!preview) {
                preview = document.createElement('div');
                preview.className = 'image-preview';
                input.parentElement.appendChild(preview);
            }
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
    
    return true;
}

function showFileError(input, message) {
    let errorSpan = input.parentElement.querySelector('.file-error');
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'file-error';
        input.parentElement.appendChild(errorSpan);
    }
    errorSpan.textContent = message;
    errorSpan.style.color = 'var(--danger-color)';
    errorSpan.style.fontSize = '12px';
    errorSpan.style.marginTop = '5px';
    input.classList.add('error');
}

function clearFileError(input) {
    const errorSpan = input.parentElement.querySelector('.file-error');
    if (errorSpan) {
        errorSpan.remove();
    }
    input.classList.remove('error');
}

// Flash Messages Auto-dismiss
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
}

// Price Formatting
function initPriceFormatting() {
    const priceElements = document.querySelectorAll('.price, .total-price');
    
    priceElements.forEach(el => {
        const price = parseFloat(el.textContent.replace(/[^0-9.-]/g, ''));
        if (!isNaN(price)) {
            el.textContent = formatPrice(price);
        }
    });
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-JM', {
        style: 'currency',
        currency: 'JMD',
        minimumFractionDigits: 2
    }).format(price);
}

// Quantity Input Validation
function initQuantityValidation() {
    const quantityInputs = document.querySelectorAll('input[type="number"][min]');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || Infinity;
            let value = parseInt(this.value);
            
            if (isNaN(value)) value = min;
            if (value < min) value = min;
            if (value > max) value = max;
            
            this.value = value;
        });
    });
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    input.error {
        border-color: var(--danger-color) !important;
    }
    
    .field-error {
        display: block;
        color: var(--danger-color);
        font-size: 12px;
        margin-top: 5px;
    }
    
    .image-preview {
        margin-top: 10px;
    }
    
    .image-preview img {
        max-width: 200px;
        border-radius: 5px;
        border: 1px solid var(--border-color);
    }
`;
document.head.appendChild(style);



document.addEventListener('DOMContentLoaded', function() {
    // --- TAB SYSTEM ---
    const tabs = document.querySelectorAll('.account-menu li');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');

            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const targetElement = document.getElementById(target);
            if (targetElement) targetElement.classList.add('active');
        });
    });

    // --- DARK MODE LOGIC ---
    const toggle = document.getElementById('dark-mode-toggle');
    const body = document.body;

    // Check if user has "Dark Mode" saved in their browser
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
        if (toggle) toggle.checked = true;
    }

    // When the user clicks the switch
    if (toggle) {
        toggle.addEventListener('change', () => {
            if (toggle.checked) {
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark'); // Save preference
            } else {
                body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light'); // Save preference
            }
        });
    }
});