/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import  PaymentButton  from "@payment/js/payment_button";  // core Odoo payment form class

// Extend the PaymentForm widget
PaymentButton.include({
    selector: '[name="o_payment_submit_button"],[name="o_payment_tokenize_container"]',
    // selector: `${PaymentButton.prototype.selector}, [name="o_payment_tokenize_checkbox"]`,
 
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

        // ✅ Add reCAPTCHA validation (for your 'custom' provider only)
        const provider = document.querySelector('input[name="o_payment_radio"]:checked');
        
        var terms_conditions=false;
        var response=false;
        if (provider && provider.dataset.providerCode === 'cibepay'){
            document.addEventListener('change', (event) => {
                if (event.target.matches('div[class="g-recaptcha"]')) {
                  response = grecaptcha.getResponse();
                console.log("Validating reCAPTCHA...");
                
                if (!response) {
                    console.log("reCAPTCHA validation failed ❌");
                    return false;
                }}

                if (terms_conditions && response) {return true;}
            });
            document.addEventListener('change', (event) => {
                if (event.target.matches('input[name="o_payment_tokenize_checkbox"]')) {
                    console.log('Terms checkbox changed:', event.target.checked);
                     terms_conditions = event.target.checked;
                    if (!terms_conditions) {
                        return false;
                    }
                }
            });
            return false;
    }


        // Everything OK
        return true;
    },
    
});
window.updateSubmit_payment = function () {
    console.log("Captcha passed ✅");
};

