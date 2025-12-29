# -*- coding: utf-8 -*-

import pprint
import requests
from odoo import models, fields, api
import json
import base64
from odoo.tools.float_utils import float_compare, float_repr, float_round
from odoo.exceptions import ValidationError

from ..models.cibepay_api import CibEPayApi
import logging

_logger = logging.getLogger(__name__)


class CibepaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cibepay", "CIB Epay")], ondelete={"cibepay": "set default"}
    )

    cibepay_username = fields.Char("User name")
    cibepay_password = fields.Char("Password")
    cibepay_terminal_id = fields.Char("Terminal ID")
    cibepay_udf1 = fields.Char("User defined value 1", default="")
    cibepay_udf2 = fields.Char("User defined value 2", default="")
    cibepay_udf3 = fields.Char("User defined value 3", default="")
    cibepay_udf4 = fields.Char("User defined value 4", default="")
    cibepay_udf5 = fields.Char("User defined value 5", default="")

    cibepay_language = fields.Selection(
        [("fr", "French"), ("ar", "Arabic"), ("en", "English")],
        string="Language",
        default="fr",
    )
    cibepay_currency = fields.Selection(
        [("012", "Algerian Dinars (DZD)")], string="Curency", default="012"
    )
    cibepay_terms_page = fields.Char("Terms and conditions page", default="terms")
    formUrl = fields.Char("formUrl", default="")

    def _get_cibepay_api(self):

        json_params = (
            '{"force_terminal_id":"'
            + self.cibepay_terminal_id
            + '", "udf1":"'
            + self.cibepay_udf1
            + '", "udf2":"'
            + self.cibepay_udf2
            + '", "udf3":"'
            + self.cibepay_udf3
            + '", "udf4":"'
            + self.cibepay_udf4
            + '", "udf5":"'
            + self.cibepay_udf5
            + '"}'
        )

        return CibEPayApi(
            self.cibepay_username,
            self.cibepay_password,
            json_params,
            self.state,
            self.cibepay_language,
            self.cibepay_currency,
        )

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "cibepay").update(
            {
                "support_tokenization": True,
            }
        )

    def _cibepay_make_request(self, endpoint, cibepay, payload=None, method="GET"):
        """Make a request to CibEpay API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        try:
            response = cibepay.SendReq(endpoint, payload)

            try:
                # response.raise_for_status()
                _logger.info("response.status_code: %s", response)

            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s",
                    endpoint,
                    pprint.pformat(payload),
                )
                raise ValidationError(
                    "CibEpay: "
                    + _(
                        "The communication with the API failed. Flutterwave gave us the following "
                        "information: '%s'",
                        response.json().get("errorMessage", ""),
                    )
                )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", endpoint)
            raise ValidationError(
                "Flutterwave: " + _("Could not establish the connection to the API.")
            )

        response = response["json_response"]

        return response
