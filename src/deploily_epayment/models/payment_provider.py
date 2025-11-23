# -*- coding: utf-8 -*-

import pprint
import requests
from odoo import models, fields, api
import json
import base64
from odoo.tools.float_utils import float_compare, float_repr, float_round
from odoo.exceptions import ValidationError

# from odoo.addons.deploily_epayment.controllers.controllers import CibEpayController

# from odoo.addons.deploily_epayment.models.cibepay_api import CibEPayApi
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

    cibepay_captcha_sitekey = fields.Char(
        "reCaptcha v2 site key", default="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    )
    cibepay_captcha_secret = fields.Char(
        "reCaptcha v2 secret key", default="6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    )
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

    # def _get_feature_support(self):
    #     """Get advanced feature support by provider.

    #     Each provider should add its technical in the corresponding
    #     key for the following features:
    #         * fees: support payment fees computations
    #         * authorize: support authorizing payment (separates
    #                      authorization and capture)
    #         * tokenize: support saving payment data in a payment.tokenize
    #                     object
    #     """
    #     res = super(CibepaymentProvider, self)._get_feature_support()
    #     res["authorize"].append("cibepay")
    #     res["tokenize"].append("cibepay")
    #     return res

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

    # @api.model
    # def cibepay_form_generate_values(self, values):
    #     # base_url = self.get_base_url()
    #     base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

    #     cibepay = self._get_cibepay_api()

    #     ref = values["reference"].split("-")
    #     order_id = ref[0]
    #     order_total = float_repr(float_round(values["amount"], 2) * 100, 0)
    #     confirm_url = base_url + CIBEPayController.confirm_url
    #     fail_url = base_url + CIBEPayController.fail_url

    #     register_params = cibepay.get_cibepay_register_params(
    #         order_id, order_total, confirm_url, fail_url
    #     )

    #     status = register_params["returnCode"]

    #     if status != 200:
    #         raise ValidationError(
    #             "Server access error! Please contact the site administrator."
    #         )

    #     # TODO Handle this error
    #     # odoo.addons.payment_cib_ipay.models.cibepay_api:
    #     # {"errorCode":"1","errorMessage":"Order number is duplicated, order with given order number is processed already"}
    #     # WARNING odoo.http: Request error! Please contact the site administrator.

    #     if register_params["errorCode"] != "0":
    #         raise ValidationError(
    #             "Request error! Please contact the site administrator."
    #         )

    #     self.formUrl = register_params["formUrl"]

    #     cibepay_tx_values = dict(values)
    #     cibepay_tx_values.update({"mdOrder": register_params["satimOrderId"]})

    #     return cibepay_tx_values

    # @api.model
    # def cibepay_get_form_action_url(self):
    #     self.ensure_one()
    #     return self.formUrl

    # todo The new functiçon
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
            _logger.info("aaaaaaaaaaaaaaaaaaaaaaaapayload %s gggg %s", payload, self)
            # cibepay = self._get_cibepay_api()
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
