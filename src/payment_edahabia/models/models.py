# -*- coding: utf-8 -*-
# © 2021 SARL TransformaTek (<https://transformatek.dz/>)
# Licence : Odoo Proprietary License v1.0 (see LICENCE)

from odoo import models, fields, api, _
import json
import base64
from urllib.parse import quote_plus
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare, float_repr, float_round

from odoo.addons.payment_edahabia.controllers.controllers import EdahabiaController
from odoo.addons.payment_edahabia.models.edahabia_api import EdahabiaApi

import logging

_logger = logging.getLogger(__name__)


class AcquirerEdahabia(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("edahabia", "Edahabia")], ondelete={"edahabia": "set default"}
    )

    edahabia_username = fields.Char("User name")
    edahabia_password = fields.Char("Password")
    edahabia_terminal_id = fields.Char("Terminal ID", default="")
    edahabia_udf1 = fields.Char("User defined value 1", default="")
    edahabia_udf2 = fields.Char("User defined value 2", default="")
    edahabia_udf3 = fields.Char("User defined value 3", default="")
    edahabia_udf4 = fields.Char("User defined value 4", default="")
    edahabia_udf5 = fields.Char("User defined value 5", default="")
    edahabia_captcha_sitekey = fields.Char(
        "reCaptcha v2 site key", default="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    )
    edahabia_captcha_secret = fields.Char(
        "reCaptcha v2 secret key", default="6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    )
    edahabia_language = fields.Selection(
        [("fr", "French"), ("ar", "Arabic"), ("en", "English")],
        string="Language",
        default="fr",
    )
    edahabia_currency = fields.Selection(
        [("012", "Algerian Dinars (DZD)")], string="Curency", default="012"
    )
    edahabia_terms_page = fields.Char("Terms and conditions page", default="terms")
    formUrl = fields.Char("formUrl", default="")

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerEdahabia, self)._get_feature_support()
        res["authorize"].append("edahabia")
        res["tokenize"].append("edahabia")
        return res

    def _get_edahabia_api(self):

        json_params = ""

        edahabia_is_testing_mode = "test" if self.state == "test" else "production"

        return EdahabiaApi(
            self.edahabia_username,
            self.edahabia_password,
            json_params,
            edahabia_is_testing_mode,
            self.edahabia_language,
            self.edahabia_currency,
        )

    @api.model
    def edahabia_form_generate_values(self, values):
        base_url = self.get_base_url()

        edahabia = self._get_edahabia_api()

        ref = values["reference"].split("-")
        order_id = ref[0]
        order_total = float_repr(float_round(values["amount"], 2) * 100, 0)
        confirm_url = base_url + EdahabiaController.confirm_url
        fail_url = base_url + EdahabiaController.fail_url

        register_params = edahabia.get_edahabia_register_params(
            order_id, order_total, confirm_url, fail_url
        )

        status = register_params["returnCode"]

        if status != 200:
            raise ValidationError(
                "Server access error! Please contact the site administrator."
            )

        if register_params["errorCode"] != "0":
            raise ValidationError(
                "Register Request Error {} : {}".format(
                    register_params["errorCode"], register_params["errorMessage"]
                )
            )

        self.formUrl = register_params["formUrl"]

        edahabia_tx_values = dict(values)
        edahabia_tx_values.update({"mdOrder": register_params["edahabiaOrderId"]})

        return edahabia_tx_values

    @api.model
    def edahabia_get_form_action_url(self):
        self.ensure_one()
        return self.formUrl


class PaymentTransactionEdahabia(models.Model):
    _inherit = "payment.transaction"

    edahabia_mdorder = fields.Char(string="EDAHABIA order ID", readonly=True)
    edahabia_approval_code = fields.Char(string="Code d'pprobation", readonly=True)
    edahabia_order_status_description = fields.Char(
        string="Code de description de la réponse", readonly=True
    )
    edahabia_auth_code = fields.Char(string="code d'autentification", readonly=True)
    edahabia_expiration = fields.Char(string="Expiration", readonly=True)
    edahabia_cardholder_name = fields.Char(
        string="Nom du propriétaire de la carte", readonly=True
    )
    edahabia_deposit_amount = fields.Char(string="Montant déposé", readonly=True)
    edahabia_order_status = fields.Integer(
        string="Statut de la commande", readonly=True
    )
    edahabia_error_code = fields.Char(string="Code d'erreur", readonly=True)
    edahabia_error_message = fields.Char(string="Message d'erreur", readonly=True)
    edahabia_pan = fields.Char(string="PAN", readonly=True)
    edahabia_ip = fields.Char(string="IP", readonly=True)

    @api.model
    def create(self, vals):
        return super(PaymentTransactionEdahabia, self).create(vals)

    def form_feedback(self, data, acquirer_name):
        return super(PaymentTransactionEdahabia, self).form_feedback(
            data, acquirer_name
        )

    @api.model
    def _edahabia_form_get_tx_from_data(self, data):

        edahabiaOrderId = data.get("orderId")
        if not edahabiaOrderId:
            _logger.info(
                "Edahabia: received data with missing reference ({}) ".format(
                    edahabiaOrderId
                )
            )
            raise ValidationError(
                _("Edahabia: received data with missing reference ({})").format(
                    edahabiaOrderId
                )
            )

        acquirer = self.env["payment.acquirer"].search([("provider", "=", "edahabia")])
        edahabia = acquirer._get_edahabia_api()

        result = edahabia.get_payment_status(edahabiaOrderId)

        if result["returnCode"] != 200:
            raise ValidationError(
                "Server access error! Please contact the site administrator."
            )

        order_id = result["orderId"]

        self._cr.execute(
            """
                SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
                FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
            """,
            [order_id + "-%"],
        )

        query_res = self._cr.fetchone()

        reference = "{}-{}".format(order_id, -query_res[0])

        txs = self.env["payment.transaction"].search([("reference", "=", reference)])

        if not txs or len(txs) > 1:
            error_msg = _("Edahabia: received data for reference {}".format(reference))
            logger_msg = "Edahabia: received data for reference {}".format(reference)
            if not txs:
                error_msg += _("; no order found")
                logger_msg += "; no order found"
            else:
                error_msg += _("; multiple order found")
                logger_msg += "; multiple order found"
            _logger.info(logger_msg)
            raise ValidationError(error_msg)

        return txs

    def _edahabia_form_validate(self, data):

        if self.state in ["done"]:
            _logger.info(
                "Edahabia: trying to validate an already validated tx (ref {})".format(
                    self.reference
                )
            )
            return True

        edahabiaOrderId = data.get("orderId")
        acquirer = self.env["payment.acquirer"].search([("provider", "=", "edahabia")])
        edahabia = acquirer._get_edahabia_api()

        result = edahabia.get_payment_status(edahabiaOrderId)

        status = result["returnCode"]
        reference = result["orderId"]

        if status != 200:
            raise ValidationError(
                "Server access error! Please contact the site administrator."
            )

        res = {
            "acquirer_reference": reference,
            "edahabia_mdorder": result["edahabiaOrderId"],
            "edahabia_approval_code": result["approvalCode"],
            "edahabia_order_status_description": result["orderStatusDescription"],
            "edahabia_auth_code": result["authCode"],
            "edahabia_expiration": result["expiration"],
            "edahabia_cardholder_name": result["cardholderName"],
            "edahabia_deposit_amount": result["depositAmount"],
            "edahabia_order_status": result["orderStatus"],
            "edahabia_error_code": result["errorCode"],
            "edahabia_error_message": result["errorMessage"],
            "edahabia_pan": result["pan"],
        }

        if result["errorCode"] == "0" and result["orderStatus"] == 2:
            _logger.info(
                "Validated Edahabia payment for tx {}: set as done".format(reference)
            )
            date_validate = fields.Datetime.now()
            res.update(date=date_validate)
            res.update(state_message=result["orderStatusDescription"])
            self.write(res)
            self._set_transaction_done()
            self.execute_callback()
            return True

        error = "Notification d'erreur pour le paiement Edahabia : {} ! ".format(
            reference
        )
        error += result["orderStatusDescription"]

        _logger.info("Edahabia error:  {}".format(error))
        res.update(state_message=error)
        self.write(res)
        self._set_transaction_error(error)
        order = self.env["sale.order"].search([("name", "=", reference)])
        order.write({"state": "cancel"})
        return False

    def action_refund(self):
        _logger.info("call to refund")
        wiz = self.env["payment_edahabia.refund_wizard"].create(
            {
                "transaction_id": self.id,
                "order_id": self.edahabia_mdorder,
                "order_amount": float(self.edahabia_deposit_amount),
                "currency_id": self.currency_id.id,
            }
        )
        return {
            "name": "Refund",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "payment_edahabia.refund_wizard",
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }
        
