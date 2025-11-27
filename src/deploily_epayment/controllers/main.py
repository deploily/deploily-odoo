# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import hmac
import json
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CibEpayController(http.Controller):

    _return_url = "/payment/cibepay/return"
    fail_url = "payment/cibepay/fail"

    @http.route(_return_url, type="http", methods=["GET"], auth="public")
    def cibepay_return_from_checkout(self, **data):
        """Process the notification data sent by Flutterwave after redirection from checkout.

        :param dict data: The notification data.
        """
        # Handle the notification data.
        if data:
            request.env["payment.transaction"].sudo()._handle_notification_data(
                "cibepay", data
            )
        else:  # The customer cancelled the payment by clicking on the close button.
            pass  # Don't try to process this case because the transaction id was not provided.

        # Redirect the user to the status page.
        return request.redirect("/payment/status")

    @http.route(
        ["/shop/cibepay/sendbymail"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        csrf=False,
    )
    def print_saleorder(self, receiver_mail, **kwargs):
        sale_order_id = request.session.get("sale_last_order_id")
        if not sale_order_id:
            return request.redirect("/shop")

        order = request.env["sale.order"].sudo().browse(sale_order_id)
        tx = order.get_portal_last_transaction()

        from_email = order.company_id.email or "contact@mycompany.com"

        if order:
            pdf, _ = (
                request.env["ir.actions.report"]
                .sudo()
                ._render_qweb_pdf("sale.action_report_saleorder", [order.id])
            )

        attachment = (
            request.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": order.name,
                    "type": "binary",
                    "datas": base64.b64encode(pdf),
                    "store_fname": f"{order.name}.pdf",
                    "res_model": order._name,
                    "res_id": order.id,
                    "mimetype": "application/pdf",
                }
            )
        )

        body_html = f"""
            <p>{tx.cibepay_resp_code_desc}</p>
            <p>Prière de trouver ci-joint votre reçu de paiement</p>
            <p>Cordialement,</p>
            <p>{order.company_id.name}</p>
        """

        mail = (
            request.env["mail.mail"]
            .sudo()
            .create(
                {
                    "subject": "Confirmation de paiement par carte CIB",
                    "body_html": body_html,
                    "email_to": receiver_mail,
                    "email_from": from_email,
                    "attachment_ids": [(6, 0, [attachment.id])],
                }
            )
        )
        mail.sudo().send()

        _logger.info(f"Mail with receipt sent to: {receiver_mail} from: {from_email}")

        values = {"mail_address": receiver_mail}
        return request.render(
            "deploily_epayment.payment_cibepay_sale_confirmation_sendmail",
            values,
        )
