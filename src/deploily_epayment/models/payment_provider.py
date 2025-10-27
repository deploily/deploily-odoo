# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import base64
from odoo.tools.float_utils import float_compare, float_repr, float_round
from odoo.exceptions import ValidationError

from odoo.addons.deploily_epayment.controllers.controllers import CIBEPayController

from odoo.addons.deploily_epayment.models.cibepay_api import CibEPayApi

import logging

_logger = logging.getLogger(__name__)


class CibepaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cibepay", "CIB Epay")], ondelete={"cibepay": "set default"}
    )

    cibipay_username = fields.Char("User name")
    cibipay_password = fields.Char("Password")
    cibipay_terminal_id = fields.Char("Terminal ID")
    cibipay_udf1 = fields.Char("User defined value 1", default="")
    cibipay_udf2 = fields.Char("User defined value 2", default="")
    cibipay_udf3 = fields.Char("User defined value 3", default="")
    cibipay_udf4 = fields.Char("User defined value 4", default="")
    cibipay_udf5 = fields.Char("User defined value 5", default="")

    cibipay_captcha_sitekey = fields.Char(
        "reCaptcha v2 site key", default="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    )
    cibipay_captcha_secret = fields.Char(
        "reCaptcha v2 secret key", default="6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    )
    cibipay_language = fields.Selection(
        [("fr", "French"), ("ar", "Arabic"), ("en", "English")],
        string="Language",
        default="fr",
    )
    cibipay_currency = fields.Selection(
        [("012", "Algerian Dinars (DZD)")], string="Curency", default="012"
    )
    cibipay_terms_page = fields.Char("Terms and conditions page", default="terms")
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

    @api.model
    def cibepay_form_generate_values(self, values):
        # base_url = self.get_base_url()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        cibipay = self._get_cibepay_api()

        ref = values["reference"].split("-")
        order_id = ref[0]
        order_total = float_repr(float_round(values["amount"], 2) * 100, 0)
        confirm_url = base_url + CIBEPayController.confirm_url
        fail_url = base_url + CIBEPayController.fail_url

        register_params = cibipay.get_cibipay_register_params(
            order_id, order_total, confirm_url, fail_url
        )

        status = register_params["returnCode"]

        if status != 200:
            raise ValidationError(
                "Server access error! Please contact the site administrator."
            )

        # TODO Handle this error
        # odoo.addons.payment_cib_ipay.models.cibipay_api:
        # {"errorCode":"1","errorMessage":"Order number is duplicated, order with given order number is processed already"}
        # WARNING odoo.http: Request error! Please contact the site administrator.

        if register_params["errorCode"] != "0":
            raise ValidationError(
                "Request error! Please contact the site administrator."
            )

        self.formUrl = register_params["formUrl"]

        cibipay_tx_values = dict(values)
        cibipay_tx_values.update({"mdOrder": register_params["satimOrderId"]})

        return cibipay_tx_values

    @api.model
    def cibipay_get_form_action_url(self):
        self.ensure_one()
        return self.formUrl
