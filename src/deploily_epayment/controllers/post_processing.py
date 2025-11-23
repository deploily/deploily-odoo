# # Part of Odoo. See LICENSE file for full copyright and licensing details.

# import logging

# import psycopg2

# from odoo import http
# from odoo.http import request
# from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing


# class PaymentPostProcessing(PaymentPostProcessing):
#     """
#     This controller is responsible for the monitoring and finalization of the post-processing of
#     transactions.

#     It exposes the route `/payment/status`: All payment flows must go through this route at some
#     point to allow the user checking on the transactions' status, and to trigger the finalization of
#     their post-processing.
#     """

#     @http.route(
#         "/payment/status", type="http", auth="public", website=True, sitemap=False
#     )
#     def display_status(self, **kwargs):
#         """Fetch the transaction and display it on the payment status page.

#         :param dict kwargs: Optional data. This parameter is not used here
#         :return: The rendered status page
#         :rtype: str
#         """
#         monitored_tx = self._get_monitored_transaction()
#         # The session might have expired, or the transaction never existed.
#         values = {"tx": monitored_tx} if monitored_tx else {"payment_not_found": True}
#         return request.render("payment.payment_status", values)
