# -*- coding: utf-8 -*-


import json
from urllib.parse import quote
import requests
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)


class CibEPayApi:

    def __init__(
        self,
        user_name,
        password,
        json_params,
        is_testing_mode="test",
        language="fr",
        currency="012",
    ):
        self.user_name = user_name
        self.password = password
        self.language = language
        self.currency = currency
        self.is_testing_mode = is_testing_mode
        self.json_params = json_params

    def get_cibepay_urls(self, state="cib"):
        """CIB IPay URLs"""
        environment = "test" if state == "test" else "cib"
        return {
            "cibepay_register_url": f"https://test2.satim.dz/payment/rest/register.do?",
            "cibepay_confirm_order_url": f"https://test2.satim.dz/payment/rest/public/acknowledgeTransaction.do?",
            "cibepay_refund_url": f"https://{environment}2.satim.dz/payment/rest/refund.do?",
        }

    def get_cibepay_register_params(self, order_id, order_total, confirm_url, fail_url):

        result = self.sendRegisterOrder(order_id, order_total, confirm_url, fail_url)

        status = result["status"]

        if status != 200:
            return {"returnCode": status, "errorDesc": result["text_error"]}

        response = result["json_response"]

        if response["errorCode"] == "0":
            cibepay_params = {
                "returnCode": status,
                "errorCode": response["errorCode"],
                "satimOrderId": response["orderId"],
                "formUrl": response["formUrl"],
            }

        else:
            cibepay_params = {
                "returnCode": result["status"],
                "errorCode": response["errorCode"],
                "errorMessage": response["errorMessage"],
            }

        return cibepay_params

    def sendRegisterOrder(
        self, order_id, order_total, confirm_url, fail_url, description=""
    ):

        base_url = self.get_cibepay_urls(self.is_testing_mode)["cibepay_register_url"]

        params = {
            "userName": self.user_name,
            "password": self.password,
            "language": self.language,
            "currency": self.currency,
            "jsonParams": self.json_params,
            "returnUrl": confirm_url,
            "failUrl": fail_url,
            "orderNumber": order_id,
            "amount": order_total,
            "description": description,
        }

        return self.SendReq(base_url, params)

    def get_payment_status(self, satim_order_id):

        objDateTime = datetime.now(pytz.timezone("Africa/Algiers")).strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        result = self.SendConfirmOrder(satim_order_id)

        status = result["status"]

        if status != 200:
            return {"returnCode": status, "errorDesc": result["text_error"]}

        response = result["json_response"]

        payment_status = {
            "returnCode": status,
            "satimOrderId": satim_order_id,
            "orderId": response["OrderNumber"],
            "dateTime": objDateTime,
            "amount": response["Amount"] / 100.0,
            "actionCodeDescription": response["actionCodeDescription"],
            "depositAmount": response["depositAmount"] / 100.00,
            "currency": response["currency"],
            "errorCode": response["ErrorCode"],
            "errorMessage": response["ErrorMessage"],
            "actionCode": response["actionCode"],
        }

        payment_status["expiration"] = (
            response["expiration"] if "expiration" in response.keys() else ""
        )
        payment_status["cardholderName"] = (
            response["cardholderName"] if "cardholderName" in response.keys() else ""
        )
        payment_status["orderStatus"] = (
            response["OrderStatus"] if "OrderStatus" in response.keys() else ""
        )
        payment_status["pan"] = response["Pan"] if "Pan" in response.keys() else ""
        payment_status["ip"] = response["Ip"] if "Ip" in response.keys() else ""

        payment_status["svfeResponse"] = (
            response["svfeResponse"] if "svfeResponse" in response.keys() else ""
        )
        payment_status["approvalCode"] = (
            response["approvalCode"] if "approvalCode" in response.keys() else ""
        )
        payment_status["respCode_desc"] = ""
        payment_status["respCode"] = ""

        if "params" in response and response["params"]:
            params = response["params"]
            payment_status["respCode_desc"] = (
                params["respCode_desc"] if "respCode_desc" in params.keys() else ""
            )
            payment_status["respCode"] = (
                params["respCode"] if "respCode" in params.keys() else ""
            )
            payment_status["params-udf1"] = (
                params["udf1"] if "udf1" in params.keys() else ""
            )
            payment_status["params-udf2"] = (
                params["udf2"] if "udf2" in params.keys() else ""
            )
            payment_status["params-udf3"] = (
                params["udf3"] if "udf2" in params.keys() else ""
            )
            payment_status["params-udf4"] = (
                params["udf4"] if "udf4" in params.keys() else ""
            )
            payment_status["params-udf5"] = (
                params["udf5"] if "udf5" in params.keys() else ""
            )

        return payment_status

    def SendConfirmOrder(self, order_id):

        base_url = self.get_cibepay_urls(self.is_testing_mode)[
            "cibepay_confirm_order_url"
        ]

        params = {
            "userName": self.user_name,
            "password": self.password,
            "language": self.language,
            "orderId": order_id,
        }

        return self.SendReq(base_url, params)

    #
    # Business logic for REFUND
    #

    def do_refund(self, satim_order_id, amount):

        result = self.SendRefundOrder(satim_order_id, amount)

        status = result["status"]

        if status != 200:
            return {"returnCode": status, "errorDesc": result["text_error"]}

        response = result["json_response"]

        refund_status = {
            "returnCode": status,
            "satimOrderId": satim_order_id,
            "amount": amount,
            "errorCode": response["errorCode"],
            "errorMessage": response["errorMessage"],
        }

        return refund_status

    def SendRefundOrder(self, order_id, amount):

        base_url = self.get_cibepay_urls(self.is_testing_mode)["cibepay_refund_url"]

        params = {
            "userName": self.user_name,
            "password": self.password,
            "language": self.language,
            "currency": self.currency,
            "amount": amount,
            "orderId": order_id,
        }

        return self.SendReq(base_url, params)

    #
    # Utility function to manage HTTP server requests
    #
    def SendReq(self, url, params):

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except Exception as e:
            _logger.error(e)
            return {"status": "HTTP_ERR", "text_error": e}

        status_code = response.status_code

        # Check for errors
        if status_code == requests.codes.ok:
            # Success
            _logger.info(response.text)
            return {"status": 200, "json_response": json.loads(response.text)}
        else:
            _logger.error(response.text)
            return {"status": "ERR", "text_error": response.text}
