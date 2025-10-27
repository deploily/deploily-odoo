# -*- coding: utf-8 -*-


import base64
import json
import werkzeug

from odoo import http
from odoo.http import request
import requests

import logging

_logger = logging.getLogger(__name__)


class CIBEPayController(http.Controller):
    confirm_url = "payment/cibepay/confirm/"
    fail_url = "payment/cibepay/fail/"

    @http.route(
        ["/payment/cibepay/confirm/", "/payment/cibepay/fail/"],
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def cibepay_form_feedback(self, **kwargs):
        """CIBEPay confirm / fail"""
        _logger.info("CIBEPay: entering form_feedback with data {}".format(kwargs))
        request.env["payment.transaction"].sudo().form_feedback(kwargs, "cibepay")
        return werkzeug.utils.redirect("/payment/process")

    # @http.route(['/payment/cibepay/refund/request'], type='http', auth="public", website=True, sitemap=False )
    def refund_request(self, **kwargs):
        return request.render("deploily_epayment.payment_cibepay_refund")

    # @http.route(['/payment/cibepay/refund/status'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def refund_status(self, order_id, amount, **kwargs):

        provider = (
            request.env["payment.provider"].sudo().search([("code", "=", "cibepay")])
        )
        cibepay = provider._get_cibepay_api()

        amount_currency = int(amount) * 100
        satim_order_id = order_id.strip()
        result = cibepay.do_refund(satim_order_id, amount_currency)

        if result["returnCode"] != 200:
            _logger.info(
                "SATIM server request error ("
                + result["returnCode"]
                + ") : "
                + result["text_error"]
            )
            return request.redirect("/payment/cibepay/refund/request")

        error_code = result["errorCode"]
        message = result["errorMessage"]

        values = {"refund_status": message, "refund_response_code": error_code}

        return request.render("deploily_epayment.payment_cibepay_refund_status", values)

    @http.route(
        ["/shop/cibepay/sendbymail"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        csrf=False,
    )
    def print_saleorder(self, receiver_mail, **kwargs):
        sale_order_id = request.session.get("sale_last_order_id")

        if sale_order_id:
            order = (
                request.env["sale.order"]
                .sudo()
                .search([("id", "=", sale_order_id)], limit=1)
            )
            tx = order.get_portal_last_transaction()

            from_email = "contact@mycompany.com"
            if order.company_id.email:
                from_email = order.company_id.email

            pdf, _ = (
                request.env.ref("sale.action_report_saleorder")
                .sudo()
                ._render_qweb_pdf([sale_order_id])
            )

            attachment = (
                request.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": order.name,
                        "type": "binary",
                        "datas": base64.b64encode(pdf),
                        "store_fname": order.name + ".pdf",
                        "res_model": order._name,
                        "res_id": order.id,
                        "mimetype": "application/x-pdf",
                    }
                )
            )

            values = {"mail_address": receiver_mail}

            mail_obj = request.env["mail.mail"]
            body_html = "<p>" + tx.cibepay_resp_code_desc + "</p>"
            body_html += "<p>Prière de trouver ci-joint votre reçu de paiement</p>"
            body_html += "<p>Cordialemet</p>"
            body_html += "<p>" + order.company_id.name + "</p>"

            mail_obj.sudo().create(
                {
                    "subject": "Confirmation de payement par carte CIB",
                    "body_html": body_html,
                    "email_to": receiver_mail,
                    "email_from": order.company_id.email,
                    "attachment_ids": [attachment.id],
                }
            )
            mail_obj.send()
            _logger.info(
                "Mail with receipt sent to: "
                + receiver_mail
                + " from: "
                + order.company_id.email
            )

            return request.render(
                "deploily_epayment.payment_cibepay_sale_confirmation_sendmail", values
            )
        else:
            return request.redirect("/shop")

    @http.route(
        ["/payment/cibepay/transaction"], type="json", auth="public", website=True
    )
    def cibepay_payment_transaction(
        self,
        acquirer_id,
        final_prepare_tx_url,
        check_terms,
        captcha,
        save_token=False,
        so_id=None,
        access_token=None,
        token=None,
        **kwargs
    ):

        website = request.website.get_current_website()
        # base_url = website.get_base_url()
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")

        formPayement = '<input type="hidden" name="data_set" data-action-url="{}/shop/payment" data-remove-me="" />'.format(
            base_url
        )

        if not captcha or not check_terms:
            _logger.info("CIBEPay captcha or terms and conditions not checked !")
            return formPayement

        captcha_verified = self._check_google_recaptcha(captcha)

        if not captcha_verified:
            _logger.info("CIBEPay cannot authentify captcha !")
            return formPayement

        # return formPayement

        params = {
            "provider_id": acquirer_id,
            "save_token": save_token,
            "so_id": so_id,
            "access_token": access_token,
            "token": token,
        }
        params.update(kwargs)

        url = base_url + final_prepare_tx_url

        headers = request.httprequest.headers

        response = requests.post(
            url, headers=headers, data=json.dumps({"params": params})
        )

        json_response = json.loads(response.text)
        return json_response.get("result", {})

    def _check_google_recaptcha(self, client_key):

        acquirer = (
            request.env["payment.provider"].sudo().search([("code", "=", "cibepay")])
        )

        secret_key = acquirer.cibepay_captcha_secret

        captcha_data = {"secret": secret_key, "response": client_key}

        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify", data=captcha_data
        )
        response = json.loads(r.text)
        return response["success"]
