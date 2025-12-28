# -*- coding: utf-8 -*-

import logging
import pprint
import html
from odoo.http import request

from ..controllers.main import CibEpayController
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_repr, float_round

_logger = logging.getLogger(__name__)


class PaymentTransactionCibIPay(models.Model):
    _inherit = "payment.transaction"

    cibepay_mdorder = fields.Char(string="SATIM order ID", readonly=True)

    cibepay_approval_code = fields.Char(string="Code d'pprobation", readonly=True)
    cibepay_action_code_description = fields.Char(
        string="Code de description d'action", readonly=True
    )
    cibepay_auth_code = fields.Char(string="code d'autentification", readonly=True)
    cibepay_expiration = fields.Char(string="Expiration", readonly=True)
    cibepay_cardholder_name = fields.Char(
        string="Nom du propriétaire de la carte", readonly=True
    )
    cibepay_deposit_amount = fields.Char(string="Montant déposé", readonly=True)
    cibepay_order_status = fields.Integer(string="Statut de la commande", readonly=True)
    cibepay_error_code = fields.Char(string="Code d'erreur", readonly=True)
    cibepay_error_message = fields.Char(string="Message d'erreur", readonly=True)
    cibepay_action_code = fields.Char(string="Code d'action", readonly=True)
    cibepay_pan = fields.Char(string="PAN", readonly=True)
    cibepay_ip = fields.Char(string="IP", readonly=True)
    cibepay_svfe_response = fields.Char(string="Réponse SVFE", readonly=True)
    cibepay_resp_code_desc = fields.Char(
        string="Description du code de réponse", readonly=True
    )
    cibepay_resp_code = fields.Char(string="Code de réponse", readonly=True)
    provider_code = fields.Selection(
        related="provider_id.code",
        store=False,
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return Flutterwave-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """

        if self.provider_code != "cibepay":
            res = super()._get_specific_rendering_values(processing_values)
            return res

        # Initiate the payment and retrieve the payment link data.
        base_url = self.provider_id.get_base_url()
        cibepay = self.provider_id._get_cibepay_api()
        url = cibepay.get_cibepay_urls(cibepay.is_testing_mode)["cibepay_register_url"]
        amount = float_repr(float_round(self.amount, 2) * 100, 0)
        return_url = (
            base_url + CibEpayController._return_url[1:]
            if CibEpayController._return_url.startswith("/")
            else CibEpayController._return_url
        )
        # ORDER ID
        ref = self.reference.split("-")
        order_id = ref[0]

        payload = {
            "userName": cibepay.user_name,
            "password": cibepay.password,
            "language": cibepay.language,
            "currency": cibepay.currency,
            "jsonParams": cibepay.json_params,
            "returnUrl": return_url,
            "failUrl": return_url,
            "orderNumber": order_id,
            "amount": amount,
            "description": "Test Payment",
        }
        payment_link_data = self.provider_id._cibepay_make_request(
            url, cibepay, payload=payload
        )

        # Extract the payment link URL and embed it in the redirect form.
        if payment_link_data and payment_link_data["errorCode"] == 0:
            rendering_values = {
                "api_url": payment_link_data["formUrl"],
                "mdOrder": payment_link_data.get("orderId"),
            }
        else:
            # todo Handle the error properly on front-end
            rendering_values = {
                "errorCode": payment_link_data["errorCode"],
                "errorMessage": payment_link_data.get("errorMessage"),
            }
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on Flutterwave data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        # tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code == "cibepay":
            # self.satim_order_id = notification_data
            satim_order_id = notification_data.get("orderId") or notification_data.get(
                "txRef"
            )
            cibepay = (
                self.env["payment.provider"]
                .sudo()
                .search([("code", "=", provider_code)], limit=1)
                ._get_cibepay_api()
            )
            result = cibepay.get_payment_status(satim_order_id)
            order_id = result["orderId"]
            self._cr.execute(
                """
                SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
                FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
            """,
                [order_id + "-%"],
            )
            reference = result["orderId"]
            query_res = self._cr.fetchone()
            if query_res:
                reference = "{}-{}".format(order_id, -query_res[0])

            tx = self.search(
                [
                    ("reference", "=", reference),
                    ("provider_code", "=", "cibepay"),
                ]
            )
            tx.write(
                {
                    "cibepay_mdorder": satim_order_id if satim_order_id else False,
                    "cibepay_approval_code": (
                        result["approvalCode"] if "approvalCode" in result else False
                    ),
                    "cibepay_action_code_description": (
                        result["actionCodeDescription"]
                        if "actionCodeDescription" in result
                        else False
                    ),
                    "cibepay_auth_code": (
                        result["authorizationResponseId"]
                        if "authorizationResponseId" in result
                        else False
                    ),
                    "cibepay_expiration": (
                        result["expiration"] if "expiration" in result else False
                    ),
                    "cibepay_cardholder_name": (
                        result["cardholderName"]
                        if "cardholderName" in result
                        else False
                    ),
                    "cibepay_deposit_amount": (
                        result["depositAmount"] if "depositAmount" in result else False
                    ),
                    "cibepay_order_status": (
                        result["orderStatus"] if "orderStatus" in result else False
                    ),
                    "cibepay_error_code": (
                        result["errorCode"] if "errorCode" in result else False
                    ),
                    "cibepay_error_message": (
                        result["errorMessage"] if "errorMessage" in result else False
                    ),
                    "cibepay_action_code": (
                        result["actionCode"] if "actionCode" in result else False
                    ),
                    "cibepay_pan": result["pan"] if "pan" in result else False,
                    "cibepay_ip": result["ip"] if "ip" in result else False,
                    "cibepay_svfe_response": (
                        result["svfeResponse"] if "svfeResponse" in result else False
                    ),
                    "cibepay_resp_code_desc": (
                        result["respCode_desc"] if "respCode_desc" in result else False
                    ),
                    "cibepay_resp_code": (
                        result["respCode"] if "respCode" in result else False
                    ),
                }
            )
            if (
                result["errorCode"] == "2"
                and result["orderStatus"] == 2
                and result["respCode"] == "00"
            ):
                tx._set_done()
                return tx
            error = "Notification d'erreur pour Paiement CIBIPay : {} !".format(
                reference
            )
            if (
                result["orderStatus"] == 3
                and result["errorCode"] == "0"
                and result["respCode"] == "00"
            ):
                error += "Votre transaction a été rejetée / Your transaction was rejected / تم رفض معاملتك <br/>"
            elif not result["respCode_desc"]:
                error += result["actionCodeDescription"]
            else:
                error += result["respCode_desc"]

            tx._set_error(error)
            order = self.env["sale.order"].search([("name", "=", reference)])
            order.write({"state": "cancel"})
            new_order = order.sudo().copy(
                {
                    "state": "draft",
                }
            )
            return tx
        return self
