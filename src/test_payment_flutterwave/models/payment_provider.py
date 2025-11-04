# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import pprint

import requests
from werkzeug.urls import url_join

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.const import REPORT_REASONS_MAPPING
from odoo.addons.test_payment_flutterwave import const
from odoo.addons.payment_flutterwave.models.payment_provider import PaymentProvider


_logger = logging.getLogger(__name__)


class TestPaymentProvider(PaymentProvider):
    _inherit = "payment.provider"

    # === COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        super()._compute_feature_support_fields()
        _logger.info("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.filtered(lambda p: p.code == "flutterwave").update(
            {
                "support_tokenization": True,
            }
        )

    # === BUSINESS METHODS ===#

    @api.model
    def _get_compatible_providers(
        self, *args, is_validation=False, report=None, **kwargs
    ):
        _logger.info("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

        """Override of `payment` to filter out Flutterwave providers for validation operations."""
        providers = super()._get_compatible_providers(
            *args, is_validation=is_validation, report=report, **kwargs
        )

        if is_validation:
            unfiltered_providers = providers
            providers = providers.filtered(lambda p: p.code != "flutterwave")
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING["validation_not_supported"],
            )

        return providers

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "flutterwave":
            _logger.info("ccccccccccccccccccccccccccccccccccccccccccccccccc")

            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _flutterwave_make_request(self, endpoint, payload=None, method="GET"):
        """Make a request to Flutterwave API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()
        payload = {
            "userName": "SAT2510260704",
            "password": "satim120",
            "language": "fr",
            "currency": "012",
            "jsonParams": "{'force_terminal_id':'E010902021','udf1':'2018105301346','udf5':'ggsf85s42524s5uhgsf'}".replace(
                "'", '"'
            ),
            "returnUrl": "https://example.com/payment/return",
            "failUrl": "https://example.com/payment/fail",
            "orderNumber": "12344pqw",
            "amount": "10000",
            "description": "Test Payment",
        }

        url = "https://test2.satim.dz/payment/rest/register.do"
        # headers = {"Authorization": f"Bearer {self.flutterwave_secret_key}"}

        try:
            _logger.info("aaaaaaaaaaaaaaaaaaaaaaaapayload %s gggg %s", payload, self)
            response = self.SendReq(url, payload)

            try:
                # response.raise_for_status()
                _logger.info("response.status_code: %s", response)
                status = response["status"]

            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s",
                    url,
                    pprint.pformat(payload),
                )
                raise ValidationError(
                    "Flutterwave: "
                    + _(
                        "The communication with the API failed. Flutterwave gave us the following "
                        "information: '%s'",
                        response.json().get("message", ""),
                    )
                )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "Flutterwave: " + _("Could not establish the connection to the API.")
            )

        response = response["json_response"]

        if response["errorCode"] == 0:
            cibipay_params = {
                "returnCode": status,
                "errorCode": response["errorCode"],
                "satimOrderId": response["orderId"],
                "formUrl": response["formUrl"],
            }

        else:
            cibipay_params = {
                # "returnCode": response["status"],
                "errorCode": response["errorCode"],
                "errorMessage": response["errorMessage"],
            }

        return cibipay_params
        # return response.json()

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "flutterwave":
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def SendReq(self, url, params):

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except Exception as e:
            _logger.error(e)
            return {"status": "HTTP_ERR", "text_error": e}

        status_code = response.status_code

        # Check for errors
        if status_code == requests.codes.ok:
            # Success
            _logger.info(response.text)
            return {"status": 200, "json_response": json.loads(response.text)}
        else:
            _logger.error(response.text)
            return {"status": "ERR", "text_error": response.text}
