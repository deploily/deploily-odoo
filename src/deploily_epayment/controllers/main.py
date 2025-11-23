# Part of Odoo. See LICENSE file for full copyright and licensing details.

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
        _logger.info(
            "zzzzzzzzzzzzzzzzzzzzzzzz i am in flutterwave_return_from_checkout"
        )
        _logger.info(
            "Handling redirection from Flutterwave with data:\n%s",
            pprint.pformat(data),
        )
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
