# -*- coding: utf-8 -*-
# © 2021 SARL TransformaTek (<https://transformatek.dz/>)
# Licence : Odoo Proprietary License v1.0 (see LICENCE)

from odoo import models, fields, api, _
import json
import base64
from urllib.parse import quote_plus
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare, float_repr, float_round

from odoo.addons.payment_cib_ipay.controllers.controllers import CIBIPayController
from odoo.addons.payment_cib_ipay.models.cibipay_api import CibIPayApi

import logging
_logger = logging.getLogger(__name__)

class AcquirerCIBIPay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cibipay', "CIBIPay")], 
                                ondelete={'cibipay': 'set default'})
        
    cibipay_username = fields.Char("User name") 
    cibipay_password = fields.Char("Password") 
    cibipay_terminal_id = fields.Char("Terminal ID") 
    cibipay_udf1 = fields.Char("User defined value 1", default="")
    cibipay_udf2 = fields.Char("User defined value 2", default="")
    cibipay_udf3 = fields.Char("User defined value 3", default="")
    cibipay_udf4 = fields.Char("User defined value 4", default="")
    cibipay_udf5 = fields.Char("User defined value 5", default="")
    cibipay_captcha_sitekey = fields.Char("reCaptcha v2 site key", 
                                    default="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
    cibipay_captcha_secret = fields.Char("reCaptcha v2 secret key", 
                                    default="6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
    cibipay_language = fields.Selection([('fr', 'French'), ('ar', 'Arabic'), ('en', 'English')], 
                                        string="Language", default='fr')
    cibipay_currency = fields.Selection([('012', 'Algerian Dinars (DZD)')], 
                                        string="Curency", default='012')
    cibipay_terms_page = fields.Char('Terms and conditions page', default="terms")
    formUrl = fields.Char('formUrl', default="")
    
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
        res = super(AcquirerCIBIPay, self)._get_feature_support()
        res['authorize'].append('cibipay')
        res['tokenize'].append('cibipay')
        return res

    def _get_cibipay_api(self):
        
        json_params = '{"force_terminal_id":"' + self.cibipay_terminal_id \
                            + '", "udf1":"' + self.cibipay_udf1 \
                            + '", "udf2":"' + self.cibipay_udf2 \
                            + '", "udf3":"' + self.cibipay_udf3 \
                            + '", "udf4":"' + self.cibipay_udf4 \
                            + '", "udf5":"' + self.cibipay_udf5 + '"}'

        return CibIPayApi(self.cibipay_username, 
                                    self.cibipay_password, 
                                    json_params,
                                    self.state, 
                                    self.cibipay_language, 
                                    self.cibipay_currency)

    @api.model
    def cibipay_form_generate_values(self, values):
        # base_url = self.get_base_url()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        cibipay = self._get_cibipay_api()
        
        ref = values['reference'].split('-')
        order_id = ref[0]
        order_total = float_repr(float_round(values['amount'], 2) * 100, 0)
        confirm_url = base_url + CIBIPayController.confirm_url
        fail_url = base_url + CIBIPayController.fail_url
        
        register_params = cibipay.get_cibipay_register_params(order_id, order_total, 
                                                              confirm_url, fail_url)
        
        status = register_params['returnCode']
        
        if (status != 200):
            raise ValidationError("Server access error! Please contact the site administrator.")

        # TODO Handle this error 
        # odoo.addons.payment_cib_ipay.models.cibipay_api: 
        # {"errorCode":"1","errorMessage":"Order number is duplicated, order with given order number is processed already"} 
        # WARNING odoo.http: Request error! Please contact the site administrator. 
        
        if (register_params['errorCode'] != "0"):
            raise ValidationError("Request error! Please contact the site administrator.")

        self.formUrl = register_params['formUrl']        
        
        cibipay_tx_values = dict(values)
        cibipay_tx_values.update({
            'mdOrder': register_params['satimOrderId']
        })

        return cibipay_tx_values
    
    @api.model
    def cibipay_get_form_action_url(self):
        self.ensure_one()
        return self.formUrl

    
class PaymentTransactionCibIPay(models.Model):
    _inherit = 'payment.transaction'

    cibipay_mdorder = fields.Char(string='SATIM order ID', readonly=True)
    cibipay_approval_code = fields.Char(string="Code d'pprobation", readonly=True)
    cibipay_action_code_description = fields.Char(string="Code de description d'action", readonly=True)
    cibipay_auth_code = fields.Char(string="code d'autentification", readonly=True)
    cibipay_expiration = fields.Char(string="Expiration", readonly=True)
    cibipay_cardholder_name = fields.Char(string="Nom du propriétaire de la carte", readonly=True)
    cibipay_deposit_amount = fields.Char(string="Montant déposé", readonly=True)
    cibipay_order_status = fields.Integer(string="Statut de la commande", readonly=True)
    cibipay_error_code = fields.Char(string="Code d'erreur", readonly=True)
    cibipay_error_message = fields.Char(string="Message d'erreur", readonly=True)
    cibipay_action_code = fields.Char(string="Code d'action", readonly=True)
    cibipay_pan = fields.Char(string="PAN", readonly=True)
    cibipay_ip = fields.Char(string="IP", readonly=True)
    cibipay_svfe_response = fields.Char(string="Réponse SVFE", readonly=True)
    cibipay_resp_code_desc = fields.Char(string="Description du code de réponse", readonly=True)
    cibipay_resp_code = fields.Char(string="Code de réponse", readonly=True)

    @api.model
    def create(self, vals):
        return super(PaymentTransactionCibIPay, self).create(vals)

    def form_feedback(self, data, acquirer_name):
        return super(PaymentTransactionCibIPay, self).form_feedback(data, acquirer_name)
    
    @api.model
    def _cibipay_form_get_tx_from_data(self, data):
        
        satimOrderId = data.get('orderId')
        if not satimOrderId :
            _logger.info('CIBIPay: received data with missing reference ({}) '.format(satimOrderId))
            raise ValidationError(_('CIBIPay: received data with missing reference ({})').format(satimOrderId))

        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'cibipay')])
        cibipay = acquirer._get_cibipay_api()
        
        result = cibipay.get_payment_status(satimOrderId)

        if (result['returnCode'] != 200):
            raise ValidationError("Server access error! Please contact the site administrator.")

        order_id = result['orderId']

        self._cr.execute('''
                SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
                FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
            ''', [order_id + '-%'])
        
        query_res = self._cr.fetchone()
        
        reference = "{}-{}".format(order_id, -query_res[0])

        txs = self.env['payment.transaction'].search([('reference', '=', reference)])

        if not txs or len(txs) > 1:
            error_msg = _('CIBIPay: received data for reference {}'.format(reference))
            logger_msg = 'CIBIPay: received data for reference {}'.format(reference)
            if not txs:
                error_msg += _('; no order found')
                logger_msg += '; no order found'
            else:
                error_msg += _('; multiple order found')
                logger_msg += '; multiple order found'
            _logger.info(logger_msg)
            raise ValidationError(error_msg)

        return txs

    def _cibipay_form_validate(self, data):

        if self.state in ['done']:
            _logger.info('CIBIpay: trying to validate an already validated tx (ref {})'.format(self.reference))
            return True

        satimOrderId = data.get('orderId')
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'cibipay')])
        cibipay = acquirer._get_cibipay_api()
        
        result = cibipay.get_payment_status(satimOrderId)

        status = result['returnCode']
        reference = result['orderId']
        
        if (status != 200):
            raise ValidationError("Server access error! Please contact the site administrator.")
            
        res = {
            'acquirer_reference': reference,
            'cibipay_mdorder' : result['satimOrderId'],
            'cibipay_approval_code':result['approvalCode'],
            'cibipay_action_code_description':result['actionCodeDescription'],
            'cibipay_auth_code' :result['authCode'],
            'cibipay_expiration':result['expiration'],
            'cibipay_cardholder_name':result['cardholderName'],
            'cibipay_deposit_amount':result['depositAmount'],
            'cibipay_order_status':result['orderStatus'],
            'cibipay_error_code':result['errorCode'],
            'cibipay_error_message':result['errorMessage'],
            'cibipay_action_code':result['actionCode'],
            'cibipay_pan':result['pan'],
            'cibipay_ip':result['ip'],
            'cibipay_svfe_response':result['svfeResponse'],
            'cibipay_resp_code_desc':result['respCode_desc'],
            'cibipay_resp_code':result['respCode'],
        }

        if result['errorCode'] == '2' and result['orderStatus'] == 2 and result['respCode'] == "00":
                _logger.info('Validated CIBIPay payment for tx {}: set as done'.format(reference))
                date_validate = fields.Datetime.now()
                res.update(date=date_validate)
                res.update(state_message=result['respCode_desc'])
                self.write(res)
                self._set_transaction_done()
                self.execute_callback()
                return True
        
        error = "Notification d'erreur pour Paiement CIBIPay : {} !".format(reference)
        if result['orderStatus'] == 3 and result['errorCode'] == '0' and result['respCode'] == "00" :  
                error += 'Votre transaction a été rejetée / Your transaction was rejected / تم رفض معاملتك <br/>'
        elif not result['respCode_desc'] :
            error += result['actionCodeDescription']
        else :
            error += result['respCode_desc'] 

        _logger.info('CIBIPay error:  {}'.format(error))
        res.update(state_message=error)
        self.write(res)
        self._set_transaction_error(error)
        order = self.env['sale.order'].search([('name', '=', reference)])
        order.write({ 'state': 'cancel' })
        return False

    def action_refund(self):
        _logger.info("call to refund")
        wiz = self.env["payment_cibipay.refund_wizard"].create(
            {
                "transaction_id": self.id,
                "order_id": self.cibipay_mdorder,
                "order_amount": float(self.cibipay_deposit_amount),
                "currency_id": self.currency_id.id,
            }
        )
        return {
            "name": "Refund",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "payment_cibipay.refund_wizard",
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }
        
