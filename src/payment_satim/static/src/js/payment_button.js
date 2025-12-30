/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import PaymentButton from "@payment/js/payment_button";  // core Odoo payment form class


window.updateSubmit_signup = function () {
    console.log("reCAPTCHA callback executed!");

    // Find the hidden reCAPTCHA response
    const captcha = document.querySelector('textarea[name="g-recaptcha-response"]');
    const terms = document.querySelector('#payment_terms_conditions_checkbox');
    const submitButton = document.querySelector('button[name="o_payment_submit_button"]');

    // Sanity check
    if (!submitButton) {
        console.warn("Submit button not found!");
        return;
    }

    // Check both conditions
    const captchaValid = captcha && captcha.value.trim() !== "";
    const termsValid = terms && terms.checked;

    if (captchaValid && termsValid) {
        submitButton.disabled = false;
        console.log("Button enabled — all good!");
    } else {
        submitButton.disabled = true;
        console.log("⚠️ Button disabled — waiting for conditions.");
    }
};
// Extend the PaymentForm widget
PaymentButton.include({
    selector: '[name="o_payment_submit_button"],[name="o_payment_tokenize_container"]',
    /**
     * Override _canSubmit to include reCAPTCHA validation
     * @override
     */
    _canSubmit() {
        // Call original behavior
        const canSubmit = this._super(...arguments);

        // If original validation fails (e.g. no payment selected), stop here
        if (!canSubmit) {
            return false;
        }

        const logo = document.querySelector('#cib_logo');
        const provider = document.querySelector('input[name="o_payment_radio"]:checked');
        if (provider && provider.dataset.providerCode === 'cibepay') {
            if (logo) {
                logo.classList.remove('cib-hidden');
            }
            return false;
        }
        if (logo) {
            logo.classList.add('cib-hidden');
        }

        // Everything OK
        return true;
    },

});


