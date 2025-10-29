/** @odoo-module **/

import { loadJS, loadCSS } from '@web/core/assets';
import { _t } from '@web/core/l10n/translation';
import { pyToJsLocale } from '@web/core/l10n/utils';
import paymentForm from '@payment/js/payment_form';
import { rpc, RPCError } from '@web/core/network/rpc';


paymentForm.include({
  

    /**
     * Prepare the params for the RPC to the transaction route.
     * @private
     * @param {string} captcha
     * @param {string} check_terms
     * @return {object} The transaction route params.
     */

    _prepareCibTransactionRouteParams(captcha, check_terms) {

        let transactionRouteParams = {
            'provider_id': this.paymentContext.providerId,
            'payment_method_id': this.paymentContext.paymentMethodId ?? null,
            'token_id': this.paymentContext.tokenId ?? null,
            'amount': this.paymentContext['amount'] !== undefined
                ? parseFloat(this.paymentContext['amount']) : null,
            'flow': this.paymentContext['flow'],
            'tokenization_requested': this.paymentContext['tokenizationRequested'],
            'landing_route': this.paymentContext['landingRoute'],
            'is_validation': this.paymentContext['mode'] === 'validation',
            'access_token': this.paymentContext['accessToken'],
            'csrf_token': odoo.csrf_token,
            'register_url': "/payment/cibipay/register/",
            'check_terms': check_terms,
            'captcha': captcha
        };
        return transactionRouteParams;
    },
    /**
     * Make an RPC to initiate the payment flow by creating a new transaction.
     *
     * For a provider to do pre-processing work (e.g., perform checks on the form inputs), or to
     * process the payment flow in its own terms (e.g., re-schedule the RPC to the transaction
     * route), it must override this method.
     *
     * To alter the flow-specific processing, it is advised to override `_processRedirectFlow`,
     * `_processDirectFlow`, or `_processTokenFlow` instead.
     *
     * @override
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The payment flow of the selected payment option.
     * @return {void}
     */
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        // Create a transaction and retrieve its processing values.
        if (providerCode !== 'cibepay') {
            this._super(...arguments);
            return;
        }
        var $check_terms = document.querySelector('#payment_terms_conditions_checkbox').checked;
        var $captcha = document.querySelector('textarea[name="g-recaptcha-response"]').value.trim();
        console.log("reCAPTCHA value:", $captcha);
        console.log("Terms accepted:", $check_terms);

        console.log("Initiating CIBEPAY payment flow...");
        await rpc(
            "/payment/cibepay/transaction",
            this._prepareCibTransactionRouteParams($captcha, $check_terms),
        ).then(processingValues => {
            if (flow === 'redirect') {
                this._processRedirectFlow(
                    providerCode, paymentOptionId, paymentMethodCode, processingValues
                );
            } else if (flow === 'direct') {
                this._processDirectFlow(
                    providerCode, paymentOptionId, paymentMethodCode, processingValues
                );
            } else if (flow === 'token') {
                this._processTokenFlow(
                    providerCode, paymentOptionId, paymentMethodCode, processingValues
                );
            }
        }).catch(error => {
            if (error instanceof RPCError) {
                this._displayErrorDialog(_t("Payment processing failed"), error.data.message);
                this._enableButton(); // The button has been disabled before initiating the flow.
            }
            return Promise.reject(error);
        });

    },

});