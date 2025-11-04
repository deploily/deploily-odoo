/** @odoo-module */

import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({

    /**
     * Allow forcing redirect to authorization url for Flutterwave token flow.
     *
     * @override method from @payment/js/payment_form
   
     */
    // _processTokenFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
    _processTokenFlow() {
        console.log('hhhhhhhhhhhhhhhhhhhhh');

        // if (providerCode === 'flutterwave' && processingValues.redirect_form_html) {

        //     // Authorization uses POST instead of GET
        //     const redirect_form_html = processingValues.redirect_form_html.replace(
        //         /method="get"/, 'method="post"'
        //     )
        //     this._processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, {
        //         ...processingValues,
        //         redirect_form_html,
        //     });
        // } else {
        //     this._super(...arguments);
        // }
        console.log('Flutterwave _processTokenFlow override called');

        this._super(...arguments);

        console.log('Flutterwave _processTokenFlow override called');
    },

    /**
     * Redirect the customer by submitting the redirect form included in the processing values.
     *
     * @override
    //  * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        // Create and configure the form element with the content rendered by the server.
        console.log('Flutterwave _processRedirectFlow override called');
        const div = document.createElement('div');
        div.innerHTML = processingValues['redirect_form_html'];
        const redirectForm = div.querySelector('form');
        redirectForm.setAttribute('id', 'o_payment_redirect_form');
        redirectForm.setAttribute('target', '_top');  // Ensures redirections when in an iframe.

        // Submit the form.
        document.body.appendChild(redirectForm);
        redirectForm.submit();
    },
});
