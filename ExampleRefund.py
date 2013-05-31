__author__ = 'ragnar'

import api

api.url = "https://tweb34.handpoint.com"
api.cardAcceptor = "7f6451e8314defbb50d0"
api.sharedSecret = "8F10C8AD35B7AEC11675B50DBF6ACEAA0B4EC280B92500E51A02F7BBBE7B07C6"

paymentData = api.PaymentData(currency="USD", amount=1.00, card_number="4242424242424242", expiry_date_year="1215",
                                                                                    card_verification_code="")
response = api.doRefund(paymentData)

print('Response from Bixby: %s' % response)
