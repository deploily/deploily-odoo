# -*- coding: utf-8 -*-
# © 2021 SARL TransformaTek (<https://transformatek.dz/>)
# Licence : Odoo Proprietary License v1.0 (see LICENCE)

import json
from urllib.parse import quote
import requests
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)

class EdahabiaApi():
    		
    def __init__(self, user_name, password, json_params, 
                 is_testing_mode = "test", language = "fr", currency = "012"):
        self.user_name = user_name
        self.password = password
        self.language = language
        self.currency = currency
        self.is_testing_mode = is_testing_mode
        self.json_params = json_params 

    def get_edahabia_urls(self, state):
        """ EDAHABIA URLS:
            - standard order: POST address for form-based """
        environment = 'test' if state == 'test' else 'prod' # TODO update to production link

        return {
            "edahabia_register_url": "https://webmerchant.poste.dz/payment/rest/register.do",
            "edahabia_get_order_status_url": "https://webmerchant.poste.dz/payment/rest/getOrderStatus.do",
            "edahabia_get_order_status_extended_url": "https://webmerchant.poste.dz/payment/rest/getOrderStatusExtended.do",
            "edahabia_refund_url": "https://webmerchant.poste.dz/payment/rest/refund.do",
            "edahabia_reverse_url": "https://webmerchant.poste.dz/payment/rest/reverse.do"
        }
    
    def get_edahabia_register_params(self, order_id, order_total, confirm_url, fail_url) :
        _logger.info("------------" + order_id  + " - " + order_total  + " - " + confirm_url  + " - " + fail_url)

        result = self.sendRegisterOrder(order_id, order_total, confirm_url, fail_url)

        status = result['status']

        if (status != 200):
            return {
                'returnCode'    : status,
                'errorDesc'     : result['text_error']
            }

        response = result['json_response']

        if (response['errorCode'] == "0"):
            edahabia_params = {
            'returnCode'    : status,
            'errorCode'     : response['errorCode'],
            'edahabiaOrderId'  : response['orderId'],
            'formUrl'       : response['formUrl'],
        }

        else:
            edahabia_params = {
                'returnCode'    : result['status'],
                'errorCode'     : response['errorCode'],
                'errorMessage'  : response['errorMessage'],
            }

        return edahabia_params

    def sendRegisterOrder(self, order_id, order_total,confirm_url, fail_url, description =""):
		
        base_url = self.get_edahabia_urls(self.is_testing_mode)['edahabia_register_url']

        params  = {"userName" : self.user_name, "password" : self.password, 
                 "language" : self.language, "currency" : self.currency,
                 "jsonParams" : self.json_params, "returnUrl" : confirm_url, 
                 "failUrl"  :  fail_url, "orderNumber" : order_id, 
                 "amount" : order_total, "description" : description }
        
        return self.SendReq(base_url, params)

    
    def get_payment_status(self, edahabia_order_id) :

        objDateTime = datetime.now(pytz.timezone('Africa/Algiers')).strftime("%d/%m/%Y %H:%M:%S") 

        result = self.SendConfirmOrder(edahabia_order_id)

        status = result['status']

        if (status != 200):
            return {
                'returnCode'    : status,
                'errorDesc'     : result['text_error']
            }

        response  = result['json_response']

        payment_status= {
            'returnCode'            : status,
            'edahabiaOrderId'       : edahabia_order_id,
            'orderId' 		        : response['OrderNumber'],
            'dateTime' 		        : objDateTime,
            'amount' 			    : response['Amount'] / 100.0, # TODO currency conversion
            'orderStatusDescription': response['orderStatusDescription'],
            'authCode'              : response['authCode'],
            'expiration'            : response['expiration'],
            'cardholderName'        : response['cardholderName'],
            'depositAmount'         : response['depositAmount'] / 100.00,# TODO currency conversion
            'currency'              : response['currency'],
            'orderStatus'           : response['OrderStatus'],
            'errorCode'             : response['ErrorCode'],
            'errorMessage'          : response['ErrorMessage'],
            'pan'                   : response['Pan'],
            }
        
        payment_status['approvalCode'] = (response['approvalCode'] if 'approvalCode' in response.keys() else "")
                  
        return payment_status


    def SendConfirmOrder(self, order_id) :
        
        base_url = self.get_edahabia_urls(self.is_testing_mode)['edahabia_get_order_status_url']

        params  = {"userName" : self.user_name, "password" : self.password, 
                   "language" : self.language,  "orderId" : order_id }
        
        return self.SendReq(base_url, params)
    
    # 
    # Business logic for REFUND 
    #

    def do_refund(self, edahabia_order_id, amount) :

        result = self.SendRefundOrder(edahabia_order_id, amount)

        status = result['status']

        if (status != 200):
            return {
                'returnCode'    : status,
                'errorDesc'     : result['text_error']
            }

        response  = result['json_response']

        refund_status= {
            'returnCode'     : status,
            'edahabiaOrderId'   : edahabia_order_id,
            'amount'         : amount,
            'errorCode'      : response['errorCode'],
            'errorMessage'   : response['errorMessage']
        }

        return refund_status

    # Send a <refund-order> command to the EDAHABIA Checkout server
    # @param string $order_number the order id in the accepter system
    # @param double $amount the amount to be refunded
    # 
    # @return array the status code and body of the response
    # 
    # 
    # Value	Description (the errorCode field)
    # 0	No system error
    # 5	The user must change his password
    # 5	[orderId] is empty
    # 6	Wrong order number.
    # 7	Payment must be in a correct state.
    # 7	Wrong deposit amount (less than 1 currency unit, e.g. 1 euro).
    # 7	System error.
    # 

    def SendRefundOrder(self, order_id, amount):

        base_url = self.get_edahabia_urls(self.is_testing_mode)['edahabia_refund_url']
                 
        params  = { "userName" : self.user_name, "password" : self.password, 
                    "language" : self.language, "currency" : self.currency,
                    "amount" : amount, "orderId" : order_id }
        
        return self.SendReq(base_url, params)

    # 
    # Utility function to manage HTTP server requests   
    #

    def SendReq(self, url, params) :

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except Exception as e:
            _logger.error(e)          
            return {'status' : 'HTTP_ERR', 'text_error' : e}

        status_code = response.status_code

        # Check for errors
        if( status_code == requests.codes.ok):
            # Success
            _logger.info(response.text)          
            return {'status' : 200, 'json_response' : json.loads(response.text)}
        else:
            _logger.error(response.text)
            return {'status' : 'ERR', 'text_error' : response.text}
