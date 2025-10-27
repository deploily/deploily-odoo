# -*- coding: utf-8 -*-

import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PaymentTransactionCibIPay(models.Model):
    _inherit = "payment.transaction"

    cibipay_mdorder = fields.Char(string="SATIM order ID", readonly=True)

    cibipay_approval_code = fields.Char(string="Code d'pprobation", readonly=True)
    cibipay_action_code_description = fields.Char(
        string="Code de description d'action", readonly=True
    )
    cibipay_auth_code = fields.Char(string="code d'autentification", readonly=True)
    cibipay_expiration = fields.Char(string="Expiration", readonly=True)
    cibipay_cardholder_name = fields.Char(
        string="Nom du propriétaire de la carte", readonly=True
    )
    cibipay_deposit_amount = fields.Char(string="Montant déposé", readonly=True)
    cibipay_order_status = fields.Integer(string="Statut de la commande", readonly=True)
    cibipay_error_code = fields.Char(string="Code d'erreur", readonly=True)
    cibipay_error_message = fields.Char(string="Message d'erreur", readonly=True)
    cibipay_action_code = fields.Char(string="Code d'action", readonly=True)
    cibipay_pan = fields.Char(string="PAN", readonly=True)
    cibipay_ip = fields.Char(string="IP", readonly=True)
    cibipay_svfe_response = fields.Char(string="Réponse SVFE", readonly=True)
    cibipay_resp_code_desc = fields.Char(
        string="Description du code de réponse", readonly=True
    )
    cibipay_resp_code = fields.Char(string="Code de réponse", readonly=True)

    # @api.model
    # def create(self, vals):
    #     return super(PaymentTransactionCibIPay, self).create(vals)

    # def form_feedback(self, data, acquirer_name):
    #     return super(PaymentTransactionCibIPay, self).form_feedback(data, acquirer_name)

    # @api.model
    # def _cibipay_form_get_tx_from_data(self, data):

    #     satimOrderId = data.get("orderId")
    #     if not satimOrderId:
    #         _logger.info(
    #             "CIBIPay: received data with missing reference ({}) ".format(
    #                 satimOrderId
    #             )
    #         )
    #         raise ValidationError(
    #             _("CIBIPay: received data with missing reference ({})").format(
    #                 satimOrderId
    #             )
    #         )

    #     acquirer = self.env["payment.acquirer"].search([("provider", "=", "cibipay")])
    #     cibipay = acquirer._get_cibipay_api()

    #     result = cibipay.get_payment_status(satimOrderId)

    #     if result["returnCode"] != 200:
    #         raise ValidationError(
    #             "Server access error! Please contact the site administrator."
    #         )

    #     order_id = result["orderId"]

    #     self._cr.execute(
    #         """
    #             SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
    #             FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
    #         """,
    #         [order_id + "-%"],
    #     )

    #     query_res = self._cr.fetchone()

    #     reference = "{}-{}".format(order_id, -query_res[0])

    #     txs = self.env["payment.transaction"].search([("reference", "=", reference)])

    #     if not txs or len(txs) > 1:
    #         error_msg = _("CIBIPay: received data for reference {}".format(reference))
    #         logger_msg = "CIBIPay: received data for reference {}".format(reference)
    #         if not txs:
    #             error_msg += _("; no order found")
    #             logger_msg += "; no order found"
    #         else:
    #             error_msg += _("; multiple order found")
    #             logger_msg += "; multiple order found"
    #         _logger.info(logger_msg)
    #         raise ValidationError(error_msg)

    #     return txs

    # def _cibipay_form_validate(self, data):

    #     if self.state in ["done"]:
    #         _logger.info(
    #             "CIBIpay: trying to validate an already validated tx (ref {})".format(
    #                 self.reference
    #             )
    #         )
    #         return True

    #     satimOrderId = data.get("orderId")
    #     acquirer = self.env["payment.acquirer"].search([("provider", "=", "cibipay")])
    #     cibipay = acquirer._get_cibipay_api()

    #     result = cibipay.get_payment_status(satimOrderId)

    #     status = result["returnCode"]
    #     reference = result["orderId"]

    #     if status != 200:
    #         raise ValidationError(
    #             "Server access error! Please contact the site administrator."
    #         )

    #     res = {
    #         "acquirer_reference": reference,
    #         "cibipay_mdorder": result["satimOrderId"],
    #         "cibipay_approval_code": result["approvalCode"],
    #         "cibipay_action_code_description": result["actionCodeDescription"],
    #         "cibipay_auth_code": result["authCode"],
    #         "cibipay_expiration": result["expiration"],
    #         "cibipay_cardholder_name": result["cardholderName"],
    #         "cibipay_deposit_amount": result["depositAmount"],
    #         "cibipay_order_status": result["orderStatus"],
    #         "cibipay_error_code": result["errorCode"],
    #         "cibipay_error_message": result["errorMessage"],
    #         "cibipay_action_code": result["actionCode"],
    #         "cibipay_pan": result["pan"],
    #         "cibipay_ip": result["ip"],
    #         "cibipay_svfe_response": result["svfeResponse"],
    #         "cibipay_resp_code_desc": result["respCode_desc"],
    #         "cibipay_resp_code": result["respCode"],
    #     }

    #     if (
    #         result["errorCode"] == "2"
    #         and result["orderStatus"] == 2
    #         and result["respCode"] == "00"
    #     ):
    #         _logger.info(
    #             "Validated CIBIPay payment for tx {}: set as done".format(reference)
    #         )
    #         date_validate = fields.Datetime.now()
    #         res.update(date=date_validate)
    #         res.update(state_message=result["respCode_desc"])
    #         self.write(res)
    #         self._set_transaction_done()
    #         self.execute_callback()
    #         return True

    #     error = "Notification d'erreur pour Paiement CIBIPay : {} !".format(reference)
    #     if (
    #         result["orderStatus"] == 3
    #         and result["errorCode"] == "0"
    #         and result["respCode"] == "00"
    #     ):
    #         error += "Votre transaction a été rejetée / Your transaction was rejected / تم رفض معاملتك <br/>"
    #     elif not result["respCode_desc"]:
    #         error += result["actionCodeDescription"]
    #     else:
    #         error += result["respCode_desc"]

    #     _logger.info("CIBIPay error:  {}".format(error))
    #     res.update(state_message=error)
    #     self.write(res)
    #     self._set_transaction_error(error)
    #     order = self.env["sale.order"].search([("name", "=", reference)])
    #     order.write({"state": "cancel"})
    #     return False

    # def action_refund(self):
    #     _logger.info("call to refund")
    #     wiz = self.env["payment_cibipay.refund_wizard"].create(
    #         {
    #             "transaction_id": self.id,
    #             "order_id": self.cibipay_mdorder,
    #             "order_amount": float(self.cibipay_deposit_amount),
    #             "currency_id": self.currency_id.id,
    #         }
    #     )
    #     return {
    #         "name": "Refund",
    #         "type": "ir.actions.act_window",
    #         "view_type": "form",
    #         "view_mode": "form",
    #         "res_model": "payment_cibipay.refund_wizard",
    #         "target": "new",
    #         "res_id": wiz.id,
    #         "context": self.env.context,
    #     }
