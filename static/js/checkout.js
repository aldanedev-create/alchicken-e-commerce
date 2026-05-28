// ── Payment method toggle ─────────────────────────────────────────────────
document.querySelectorAll('input[name="payment_method"]').forEach(radio => {
    radio.addEventListener('change', function () {

        const paymentProof  = document.getElementById('paymentProof');
        const proofFile     = document.getElementById('payment_proof');
        const bankDetails   = document.getElementById('bankDetails');
        const ncb           = document.getElementById('ncbDetails');
        const scotia        = document.getElementById('scotiaDetails');
        const jmmb          = document.getElementById('jmmbDetails');
        const paypalDetails = document.getElementById('paypalDetails');
        const checkoutBtn   = document.getElementById('checkoutBtn');

        // ── Reset everything first ────────────────────────────────────────
        if (paymentProof)  paymentProof.style.display  = 'none';
        if (proofFile)     proofFile.required           = false;
        if (bankDetails)   bankDetails.style.display    = 'none';
        if (ncb)           ncb.style.display            = 'none';
        if (scotia)        scotia.style.display         = 'none';
        if (jmmb)          jmmb.style.display           = 'none';
        if (paypalDetails) paypalDetails.style.display  = 'none';

        // Reset button to default
        if (checkoutBtn) {
            checkoutBtn.textContent = 'Place Order';
            checkoutBtn.onclick     = null;
        }

        // ── PayPal ───────────────────────────────────────────────────────
        if (this.value === 'paypal') {
            if (paypalDetails) paypalDetails.style.display = 'block';
            if (paymentProof)  paymentProof.style.display  = 'block';
            if (proofFile)     proofFile.required           = true;
            return;
        }

        // ── Bank transfer ────────────────────────────────────────────────
        if (this.value.startsWith('bank_transfer')) {

            if (paymentProof) {
                paymentProof.style.display = 'block';
                proofFile.required         = true;
            }

            if (bankDetails) bankDetails.style.display = 'block';

            if (this.value === 'bank_transfer_ncb'       && ncb)    ncb.style.display    = 'block';
            if (this.value === 'bank_transfer_scotiabank' && scotia) scotia.style.display = 'block';
            if (this.value === 'bank_transfer_jmmb'       && jmmb)   jmmb.style.display   = 'block';
        }
    });
});