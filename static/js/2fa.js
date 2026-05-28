document.getElementById('resendBtn').addEventListener('click', function (e) {
    e.preventDefault();

    const btn = this;
    if (btn.disabled) return;

    btn.disabled = true;

    let seconds = 60;

    // 🔥 start countdown immediately
    btn.textContent = `Resend in ${seconds}s`;

    const interval = setInterval(() => {
        seconds--;
        btn.textContent = `Resend in ${seconds}s`;

        if (seconds <= 0) {
            clearInterval(interval);
            btn.disabled = false;
            btn.textContent = 'Resend code';
        }
    }, 1000);

    // 🔥 send request (we don't care about response anymore)
    fetch('/two-fa/resend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    }).catch(() => {
        // ❌ ignore errors completely (backend already works)
    });

    // show message
    const msg = document.getElementById('resendMessage');
    if (msg) msg.style.display = 'block';
});