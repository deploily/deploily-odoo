# Part of Odoo. See LICENSE file for full copyright and licensing details.

import html
import logging
import pprint

from werkzeug import urls
from odoo import _, fields, models
from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_flutterwave import const
from odoo.addons.payment_flutterwave.controllers.main import FlutterwaveController
from odoo.addons.payment_flutterwave.models.payment_transaction import (
    PaymentTransaction,
)
from werkzeug.urls import url_encode


_logger = logging.getLogger(__name__)


class TestPaymentTransaction(PaymentTransaction):
    _inherit = "payment.transaction"

    satim_order_id = fields.Char(string="SATIM order ID", readonly=True)

    def _get_specific_processing_values(self, processing_values):
        """Override of payment to redirect pending token-flow transactions.

        If the financial institution insists on 3-D Secure authentication, this
        override will redirect the user to the provided authorization page.

        Note: `self.ensure_one()`
        """
        res = super()._get_specific_processing_values(processing_values)
        if self._flutterwave_is_authorization_pending():
            _logger.info("wwwwwwwwwwwwwwwwwwwwwwwww %s", self.provider_reference),

            res["redirect_form_html"] = self.env["ir.qweb"]._render(
                self.provider_id.redirect_form_view_id.id,
                {"api_url": self.provider_reference},
            )
        return res

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return Flutterwave-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """

        if self.provider_code != "flutterwave":
            res = super()._get_specific_rendering_values(processing_values)
            return res

        # Initiate the payment and retrieve the payment link data.
        base_url = self.provider_id.get_base_url()

        payload = {
            "userName": "SAT2510260704",
            "password": "satim120",
            "language": "fr",
            "currency": "012",
            "jsonParams": "{'force_terminal_id':'E010902021','udf1':'2018105301346','udf5':'ggsf85s42524s5uhgsf'}",
            "returnUrl": "https://example.com/payment/return",
            "failUrl": "https://example.com/payment/fail",
            "orderNumber": "123456a",
            "amount": "10000",
            "description": "Test Payment",
        }
        _logger.info("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
        payment_link_data = self.provider_id._flutterwave_make_request(
            "payments", payload=payload
        )
        _logger.info(
            "mmmmmmmmmmmmmmmmmmmmmmmmbase_url: %s",
            html.escape(payment_link_data["formUrl"]),
        )

        # Extract the payment link URL and embed it in the redirect form.
        rendering_values = {
            "api_url": payment_link_data["formUrl"],
            "mdOrder": payment_link_data.get("satimOrderId"),
        }
        return rendering_values

    def _send_payment_request(self):
        """Override of payment to send a payment request to Flutterwave.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != "flutterwave":
            return

        # Prepare the payment request to Flutterwave.
        if not self.token_id:
            raise UserError(
                "Flutterwave: " + _("The transaction is not linked to a token.")
            )

        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        base_url = self.provider_id.get_base_url()
        # data = {
        #     "token": self.token_id.provider_ref,
        #     "email": self.token_id.flutterwave_customer_email,
        #     "amount": self.amount,
        #     "currency": self.currency_id.name,
        #     "country": self.company_id.country_id.code,
        #     "tx_ref": self.reference,
        #     "first_name": first_name,
        #     "last_name": last_name,
        #     "ip": payment_utils.get_customer_ip_address(),
        #     "redirect_url": urls.url_join(
        #         base_url, FlutterwaveController._auth_return_url
        #     ),
        # }
        data = {
            "userName": "SAT2510260704",
            "password": "satim120",
            "language": "fr",
            "currency": "012",
            "jsonParams": "{'force_terminal_id':'E010902021','udf1':'2018105301346','udf5':'ggsf85s42524s5uhgsf'}",
            "returnUrl": "https://example.com/payment/return",
            "failUrl": "https://example.com/payment/fail",
            "orderNumber": "123456",
            "amount": "10000",
            "description": "Test Payment",
        }
        _logger.info("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        # Make the payment request to Flutterwave.
        response_content = self.provider_id._flutterwave_make_request(
            "tokenized-charges", payload=data
        )

        # Handle the payment request response.
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(response_content),
        )
        self._handle_notification_data("flutterwave", response_content)

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        _logger.info("hhhhhhhhhhhhhhhhhhhhhhhh")
        _logger.info(self)
        _logger.info(provider_code)
        """Override of payment to find the transaction based on Flutterwave data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        # tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code == "flutterwave":
            # self.satim_order_id = notification_data
            reference = notification_data.get("tx_ref") or notification_data.get(
                "txRef"
            )
            tx = self.search(
                [("reference", "=", reference), ("provider_code", "=", "flutterwave")]
            )
            tx.write(
                {
                    "satim_order_id": "sfqdfsegsgrgrhrth",
                }
            )
            _logger.info("hhhhhhhhhhhhhhhhhhhhhhhh")
            _logger.info(tx)
            _logger.info(notification_data)

            return tx
        return self
        # tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        # if provider_code != "flutterwave" or len(tx) == 1:
        #     return tx

        # if not reference:
        #     raise ValidationError(
        #         "Flutterwave: " + _("Received data with missing reference.")
        #     )

        # tx = self.search(
        #     [("reference", "=", reference), ("provider_code", "=", "flutterwave")]
        # )
        # if not tx:
        #     raise ValidationError(
        #         "Flutterwave: "
        #         + _("No transaction found matching reference %s.", reference)
        #     )
        # return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Flutterwave data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        if self.provider_code == "flutterwave":

            return

    def _flutterwave_tokenize_from_notification_data(self, notification_data):
        """Create a new token based on the notification data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        """
        self.ensure_one()

        token = self.env["payment.token"].create(
            {
                "provider_id": self.provider_id.id,
                "payment_method_id": self.payment_method_id.id,
                "payment_details": notification_data["card"]["last_4digits"],
                "partner_id": self.partner_id.id,
                "provider_ref": notification_data["card"]["token"],
                "flutterwave_customer_email": notification_data["customer"]["email"],
            }
        )
        self.write(
            {
                "token_id": token,
                "tokenize": False,
            }
        )
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                "token_id": token.id,
                "partner_id": self.partner_id.id,
                "ref": self.reference,
            },
        )

    def _flutterwave_is_authorization_pending(self):
        return self.filtered_domain(
            [
                ("provider_code", "=", "flutterwave"),
                ("operation", "=", "online_token"),
                ("state", "=", "pending"),
                ("provider_reference", "ilike", "https"),
            ]
        )
