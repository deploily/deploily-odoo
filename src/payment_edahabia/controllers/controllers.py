# -*- coding: utf-8 -*-
# © 2021 SARL TransformaTek (<https://transformatek.dz/>)
# Licence : Odoo Proprietary License v1.0 (see LICENCE)

import base64
import json
import werkzeug

from odoo import http
from odoo.http import request
import requests

import logging
_logger = logging.getLogger(__name__)


class EdahabiaController(http.Controller):
    confirm_url = 'payment/edahabia/confirm/'
    fail_url = 'payment/edahabia/fail/'

    @http.route(['/payment/edahabia/confirm/', '/payment/edahabia/fail/'], 
                 type='http', auth="public", methods=['GET'], csrf=False)
    def edahabia_form_feedback(self, **kwargs):
        """ Edahabia confirm / fail """
        _logger.info('Edahabia: entering form_feedback with data {}'.format(kwargs))
        request.env['payment.transaction'].sudo().form_feedback(kwargs, 'edahabia')
        return werkzeug.utils.redirect('/payment/process')
    
    
    # @http.route(['/payment/edahabia/refund/request'], type='http', auth="public", website=True, sitemap=False )
    def refund_request(self, **kwargs):
        return request.render("payment_edahabia.payment_edahabia_refund")


    # @http.route(['/payment/edahabia/refund/status'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def refund_status(self, order_id, amount, **kwargs):
        
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'edahabia')])
        edahabia = acquirer._get_edahabia_api()
        
        amount_currency = int(amount) * 100
        edahabia_order_id = order_id.strip()
        result = edahabia.do_refund(edahabia_order_id, amount_currency)
        
        if (result['returnCode'] != 200):
            _logger.info('EDAHABIA server request error (' + result['returnCode'] + ") : " + result['text_error'])
            return request.redirect('/payment/edahabia/refund/request')
        
        error_code = result['errorCode']
        message = result['errorMessage']
        
        values = {
            'refund_status': message,
            'refund_response_code' : error_code
        }

        return request.render("payment_edahabia.payment_edahabia_refund_status", values)
    

    @http.route(['/shop/edahabia/sendbymail'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def print_saleorder(self, **kwargs):
        sale_order_id = request.session.get('sale_last_order_id')

        if sale_order_id:
            order = request.env['sale.order'].sudo().search([('id', '=', sale_order_id)], limit=1)
            tx = order.get_portal_last_transaction()
            
            pdf, _ = request.env.ref('sale.action_report_saleorder').sudo()._render_qweb_pdf([sale_order_id])
            
            attachment = request.env['ir.attachment'].sudo().create({
                'name': order.name,
                'type': 'binary',
                'datas': base64.b64encode(pdf),
                'store_fname': order.name + '.pdf',
                'res_model': order._name,
                'res_id': order.id,
                'mimetype': 'application/x-pdf'
            })
                        
            values = {'mail_address': order.partner_id.email}

            mail_obj = request.env['mail.mail']
            body_html  = "<p>" + tx.edahabia_order_status_description + "</p>"
            body_html += "<p>Prière de trouver ci-joint votre reçu de paiement</p>"
            body_html += "<p>Cordialemet</p>"
            body_html += "<p>" + order.company_id.name +"</p>"

            mail_obj.sudo().create({
                'subject': 'Confirmation de payement par carte EDAHABIA',
                'body_html': body_html,
                'email_to': order.partner_id.email,
                'email_from': order.company_id.email,
                'attachment_ids' : [attachment.id]
                })
            mail_obj.send()
            _logger.info('Mail with receipt sent to: ' + order.partner_id.email + ' from: ' + order.company_id.email)

            return request.render("payment_edahabia.payment_edahabia_sale_confirmation_sendmail", values)
        else:
            return request.redirect('/shop')

    
    @http.route(['/payment/edahabia/transaction'], type='json', auth="public", website=True)
    def edahabia_payment_transaction(self, acquirer_id, final_prepare_tx_url, check_terms, captcha, save_token=False, so_id=None, access_token=None, token=None, **kwargs):

        website = request.website.get_current_website()
        base_url = website.get_base_url()

        formPayement = ' <input type="hidden" name="data_set" data-action-url="{}/shop/payment" data-remove-me="" />'.format(base_url)
        
        if not captcha or not check_terms:
            _logger.info('Edahabia captcha or terms and conditions not checked !')
            return formPayement
        
        captcha_verified = self._check_google_recaptcha(captcha)

        if not captcha_verified :
            _logger.info('Edahabia cannot authentify captcha !')
            return formPayement

        # return formPayement
        
        params  = { 'acquirer_id': acquirer_id, 'save_token' : save_token, 'so_id' : so_id, 
                    'access_token' : access_token, 'token': token}
        params.update(kwargs)

        url = base_url + final_prepare_tx_url

        headers = request.httprequest.headers

        response = requests.post(url, headers=headers, data=json.dumps({'params' : params}))

        json_response = json.loads(response.text)
        return json_response.get('result', {})


    
    def _check_google_recaptcha(self, client_key):

        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'edahabia')])
        
        secret_key = acquirer.edahabia_captcha_secret
        
        captcha_data = {
            'secret': secret_key,
            'response': client_key
        }

        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captcha_data)			
        response = json.loads(r.text)
        return response['success']