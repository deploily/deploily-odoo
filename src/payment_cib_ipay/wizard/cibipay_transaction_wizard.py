# -*- coding: utf-8 -*-
# © 2021 SARL TransformaTek (<https://transformatek.dz/>)
# Licence : Odoo Proprietary License v1.0 (see LICENCE)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


import logging

_logger = logging.getLogger(__name__)


class CibipayRefundTransactionWizard(models.TransientModel):
    _name = "payment_cibipay.refund_wizard"

    transaction_id = fields.Integer("Transaction ID", required=True)
    order_id = fields.Char("Order ID", required=True)
    order_amount = fields.Monetary(
        "Order amount", currency_field="currency_id", required=True
    )
    amount = fields.Monetary(
        "Amount to refund", currency_field="currency_id", required=True, default=0
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", required=True, readonly=True
    )

    def action_do_refund(self):

        _logger.info("call to DO refund")

        if self.amount > self.order_amount or self.amount <= 0.0 :
            raise ValidationError(
                "Please set an amount smaller or equal than {} and greater than 0.0.".format(self.order_amount)
            )

        acquirer = (
            self.env["payment.acquirer"].sudo().search([("provider", "=", "cibipay")])
        )
        cibipay = acquirer._get_cibipay_api()

        amount_currency = int(self.amount) * 100
        cibipay_order_id = self.order_id
        result = cibipay.do_refund(cibipay_order_id, amount_currency)

        if result["returnCode"] != 200:
            _logger.info(
                "CIBIPAY server request error ("
                + result["returnCode"]
                + ") : "
                + result["text_error"]
            )
            raise ValidationError(
                "CIBIPAY server request error ({}) : '{}'".format(
                    result["returnCode"], result["text_error"]
                )
            )

        error_code = result["errorCode"]
        message = result["errorMessage"]

        Transaction = self.env["payment.transaction"].sudo()
        trans = Transaction.search([("id", "=", self.transaction_id)])
        ref = trans.reference.split("-")[0]

        self._cr.execute(
            """
                SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
                FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
            """,
            [ref + "-%"],
        )

        query_res = self._cr.fetchone()

        reference = "{}-{}".format(ref, -query_res[0] + 1)

        values = {
            "amount": -self.amount,
            "date": fields.Datetime.now(),
            "state_message": message,
            "reference": reference,
            "currency_id": self.currency_id.id,
            "partner_id": trans.partner_id.id,
            "partner_country_id": trans.partner_id.country_id.id,
            "acquirer_id": trans.acquirer_id.id,
            "type": "form",
            "acquirer_reference": reference,
            "cibipay_mdorder": trans.cibipay_mdorder,
            "cibipay_cardholder_name": trans.cibipay_cardholder_name,
            "cibipay_deposit_amount": trans.cibipay_deposit_amount,
            "cibipay_pan": trans.cibipay_pan,
            "payment_id": trans.payment_id.id,
            "cibipay_error_code": error_code,
            "cibipay_error_message": message,
        }

        values.update(state_message=message)
        refund = Transaction.create(values)

        if error_code == "0":
            refund._set_transaction_done()
            refund.execute_callback()
            _logger.info(
                "CIBIPAY refund transaction success ({}) : '{}' ".format(
                    error_code, message
                )
            )
        else:
            _logger.info(
                "CIBIPAY refund transaction error ({}) : '{}' ".format(
                    error_code, message
                )
            )
            refund._set_transaction_error(message)

        action = self.env["ir.actions.actions"]._for_xml_id(
            "payment.action_payment_transaction"
        )

        return action