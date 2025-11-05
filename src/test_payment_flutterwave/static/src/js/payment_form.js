/** @odoo-module */

import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({


    // /**
    // * Prepare the params for the RPC to the transaction route.
    // * @override
    // * @private
    // * @return {object} The transaction route params.
    // */
    // _prepareTransactionRouteParams() {
    //     const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');
    //     const providerCode = this.paymentContext.providerCode = this._getProviderCode(
    //         checkedRadio
    //     );
    //     transactionRouteParams = this._super(...arguments);
    //     if (providerCode == 'flutterwave') {
    //         Object.assign(transactionRouteParams, {
    //             'satim_order_id': satim_order_id
    //         });
    //     }

    //     return transactionRouteParams;
    // },

});
