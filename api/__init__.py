__author__ = 'ragnar'
from httplib import HTTPSConnection
from httplib import HTTPConnection
from urlparse import urlparse
from urllib import urlencode
from time import gmtime, strftime
from xml.dom.minidom import Document, parseString
from hmac import new as hmac
import sha
#Pre: url_object is a object returned from urlparse()
# returns a HTTPS or HTTP connection to netloc, depending on scheme
def get_connection(url_object):
    if url_object.scheme == 'https':
        return HTTPSConnection(url_object.netloc)
    else: #http
        return HTTPConnection(url_object.netloc)


def send_post_request(url,message_type, header, body):
    send_http_request(url,message_type, header, body, 'POST')

def send_put_request(url,message_type, header, body):
    send_http_request(url,message_type, header, body, 'PUT')

# Opens a connection to a url, sends post request and returns the response.
def send_http_request(url,message_type, header, body, method):
    url_object = urlparse(url)
    connection = get_connection(url_object)
    connection.request(method, url_object.path, body, header)
    return xml_to_dict(message_type, connection.getresponse().read())


# checks if url contains '?' and/or '&' and returns a new url with param attached.
def composeUrl(url, param):
    if url.endswith('?') or url.endswith('&'):
        return url + param
    elif '?' in url and not url.endswith('&'):
        return url + '&' + param
    else:
        return url + '?' + param


# Creates a request. Used by is order_verified() & send_payment_confirmation()
def send_request(paramsDict, requestType, url, headers=None):
    params = urlencode(paramsDict)
    if headers is None:
        headers = {"Content-type": "application/x-www-form-urlencoded"}
    if requestType == 'GET':
        response = send_get_request(composeUrl(url, params))
    elif requestType == 'POST':
        response = send_post_request(url, headers, params)
    return response

# Opens a connection to a url, sends get request and returns the response.
def send_get_request(url):
    url_object = urlparse(url)
    connection = get_connection(url_object)
    connection.request('GET', '%s?%s' % (url_object.path, url_object.query))
    return connection.getresponse()

# Data class that holds headers needed for a POST to Bixby
class BixbyHeaders():
    def __init__(self, content_type, accept, date, hmac):
        self.content_type = content_type
        self.accept = accept
        self.date = date
        self.hmac = hmac

    def getHeaderDict(self):
        header = {
            'Content-type': self.content_type,
            'Accept': self.accept,
            'mws-date': self.date,
            'mws-hmac': self.hmac
        }
        return header


# Creates the headers and the body to send to Bixby. returns a headers dictionary and body xml.
def create_bixby_token(message_type,secret_key, card_acceptor, card_number, expiry_date_year,
                         token):
    now = strftime('%Y-%m-%dT%H:%M:%S%z', gmtime()).replace('-', '').replace('-', '').replace('T', '').replace(':',
                                                                                                               '').replace(
        ':', '').replace('+', '')[:-1]
    body = TokenData( card_number, expiry_date_year, token)
    hmac = get_mac(secret_key, 'PUT/%s/%s/%s%s%s' % ('tokenstore',card_acceptor,token, now, body.get_card_info_xml()))

    #'%s/tokenstore/%s/%s'% (url, cardAcceptor, TokenData.token)
    header = BixbyHeaders('text/xml', '*/*', now, hmac)
    return header.getHeaderDict(), body.get_card_info_xml()


# Creates the headers and the body to send to Bixby. returns a headers dictionary and body xml.
def create_bixby_request(message_type,secret_key, card_acceptor, currency, amount, card_number, expiry_date_month, expiry_date_year,
                         cvc):
    now = strftime('%Y-%m-%dT%H:%M:%S%z', gmtime()).replace('-', '').replace('-', '').replace('T', '').replace(':',
                                                                                                               '').replace(
        ':', '').replace('+', '')[:-1]
    body = CardData('WEB',message_type, currency, amount, card_number, expiry_date_month, expiry_date_year, cvc)
    hmac = get_mac(secret_key, 'POST/web/%s/%s%s%s' % (card_acceptor,message_type, now, body.get_card_info_xml()))
    header = BixbyHeaders('text/xml', '*/*', now, hmac)
    return header.getHeaderDict(), body.get_card_info_xml()

# Creates the headers and the body to send to Bixby. returns a headers dictionary and body xml.
def create_bixby_reversal(message_type,secret_key, card_acceptor,authorizationGuid):
    now = strftime('%Y-%m-%dT%H:%M:%S%z', gmtime()).replace('-', '').replace('-', '').replace('T', '').replace(':',
                                                                                                               '').replace(
        ':', '').replace('+', '')[:-1]
    body = ReversalData(message_type, authorizationGuid)
    hmac = get_mac(secret_key, 'POST/web/%s/%s%s%s' % (card_acceptor,message_type, now, body.get_card_info_xml()))
    header = BixbyHeaders('text/xml', '*/*', now, hmac)
    return header.getHeaderDict(), body.get_card_info_xml()


def create_bixby_cancellation(message_type,secret_key, card_acceptor, transactionType, terminalDateTime, currency, amount):

    now = strftime('%Y-%m-%dT%H:%M:%S%z', gmtime()).replace('-', '').replace('-', '').replace('T', '').replace(':',
                                                                                                               '').replace(
        ':', '').replace('+', '')[:-1]

    body = CancellationData(transactionType, terminalDateTime, currency, amount)
    hmac = get_mac(secret_key, 'POST/web/%s/%s%s%s' % (card_acceptor,message_type, now, body.get_card_info_xml()))
    header = BixbyHeaders('text/xml', '*/*', now, hmac)

    return header.getHeaderDict(), body.get_card_info_xml()


# Data class that holds all data Bixby requires for e-commerce payment
class CardData():
    def __init__(self, payment_scenario, message_type, currency, amount, card_number, expiry_date_month, expiry_date_year,
                 card_verification_code):
        self.payment_scenario = payment_scenario
        self.message_type = message_type
        self.currency = currency
        self.amount = amount
        self.card_number = card_number
        self.expiry_date = '%s%s' % ( expiry_date_month, expiry_date_year)
        self.card_verification_code = card_verification_code

    def get_card_info_xml(self):
        dict = {
            'paymentScenario': self.payment_scenario,
            'currency': self.currency,
            'amount': self.amount,
            'cardNumber': self.card_number,
            'expiryDateMMYY': self.expiry_date,
            'cardVerificationCode': self.card_verification_code
        }
        return dict_to_xml(self.message_type, dict)

# Data class that holds all data Bixby requires for e-commerce token
class TokenData():
    def __init__(self, card_number,  expiry_date_year,
                 token):
        self.card_number = card_number
        self.expiry_date_year = expiry_date_year
        self.token = token

    def get_card_info_xml(self):
        dict = {
            'cardNumber': self.card_number,
            'expiryDateMMYY': self.expiry_date_year,
            'token': self.token
        }
        return dict_to_xml('tokenStore', dict)


class ReversalData():
    def __init__(self, message_type, authorizationGuid):
        self.message_type = message_type
        self.authorizationGuid = authorizationGuid

    def get_card_info_xml(self):
        dict = {
            'authorizationGuid': self.authorizationGuid
        }
        return dict_to_xml(self.message_type, dict)



class CancellationData():
    def __init__(self, transactionType, terminalDateTime, currency, amount):
        self.transactionType = transactionType
        self.terminalDateTime = terminalDateTime
        self.currency = currency
        self.amount = amount

    def get_card_info_xml(self):
        dict = {
            'transactionType': self.transactionType,
            'terminalDateTime': self.terminalDateTime,
            'currency': self.currency,
            'amount': self.amount
        }
        return dict_to_xml('cancellation', dict)


class PaymentData():
    def __init__(self, currency, amount, card_number, expiry_date_year, card_verification_code):
        self.currency = currency
        self.amount = amount
        self.card_number = card_number
        self.expiry_date_month = expiry_date_year[:2]
        self.expiry_date_year = expiry_date_year[-2:]
        self.card_verification_code = card_verification_code



# Takes in the root element of an xml and creates a xml from the data_dict dictionary
def dict_to_xml(root_element, data_dict):
    # Create the minidom document
    doc = Document()
    root = doc.createElement(root_element)
    doc.appendChild(root)
    for item in data_dict:
        node = doc.createElement(item)
        root.appendChild(node)
        value = doc.createTextNode(str(data_dict[item]))
        node.appendChild(value)
    return doc.toxml() #toprettyxml() if needed formatted


def calc_raw_hmac_sha1(secretKey, message):
    result = hmac(secretKey, message.encode('utf-8'), sha).digest().encode('hex')
    return result


def get_mac( secretKey, message):
    return calc_raw_hmac_sha1(secretKey, message)


def getAuthorizationGuid(response_body):
    isSuccessful, dict = parseBixbyResponse(response_body)
    return dict['authorizationGuid']

def xml_to_dict(message_type, response_body):
    isSuccessful, dict = parseBixbyResponse(message_type, response_body)
    return dict


def parseBixbyResponse(message_type, xml):
    #print "about to parse xml:" ,xml
    dom = parseString( xml.encode('utf-8') )
    #the result string comming from bixby is resulting in empty text nodes being created from the xml ,
    #We have to discard of these unwanted nodes.
    root = dom.getElementsByTagName(message_type)
    if len(root) >0: #not an error
        succsessDict = {}
        for node in root[0].childNodes:
            try:
                print node.nodeName
                succsessDict[node.nodeName] = node.firstChild.data
            except:
                print "error:" ,node.nodeName
        print succsessDict
        return True, succsessDict

    else:
        root = dom.getElementsByTagName("errors")
        errDict = {}
        for node in root[0].childNodes:
            try:
                errDict[node.nodeName] = node.firstChild.data
            except:
                print "error parsing: ", node.nodeName
        print errDict
        return False, errDict


#Configuration parameters
url = "none"
cardAcceptor = "none"
sharedSecret = "none"


def authorize(PaymentData):
    bixbyRequestHeader, bixbyRequestBody = create_bixby_request('authorization', sharedSecret, cardAcceptor, PaymentData.currency,
                                                                "%.2f" % PaymentData.amount, PaymentData.card_number,
                                                                PaymentData.expiry_date_month,
                                                                PaymentData.expiry_date_year,
                                                                PaymentData.card_verification_code)
    return send_post_request('%s/web/%s/authorization' % (url, cardAcceptor),'authorization', bixbyRequestHeader, bixbyRequestBody)


def storeToken(TokenData):
    bixbyRequestHeader, bixbyRequestBody = create_bixby_token('tokenStore', sharedSecret, cardAcceptor,
                                                                TokenData.card_number,
                                                                TokenData.expiry_date_year,
                                                                TokenData.token)
    return send_put_request('%s/tokenstore/%s/%s'% (url, cardAcceptor, TokenData.token),'tokenStore', bixbyRequestHeader, bixbyRequestBody)


def doPayment(PaymentData):
    bixbyRequestHeader, bixbyRequestBody = create_bixby_request('payment', sharedSecret, cardAcceptor, PaymentData.currency,
                                                                "%.2f" % PaymentData.amount, PaymentData.card_number,
                                                                PaymentData.expiry_date_month,
                                                                PaymentData.expiry_date_year,
                                                                PaymentData.card_verification_code)
    return send_post_request('%s/web/%s/payment' % (url, cardAcceptor),'payment', bixbyRequestHeader, bixbyRequestBody)

def doRefund(PaymentData):
    bixbyRequestHeader, bixbyRequestBody = create_bixby_request('refund', sharedSecret, cardAcceptor, PaymentData.currency,
                                                                "%.2f" % PaymentData.amount, PaymentData.card_number,
                                                                PaymentData.expiry_date_month,
                                                                PaymentData.expiry_date_year,
                                                                PaymentData.card_verification_code)
    return send_post_request('%s/web/%s/refund' % (url, cardAcceptor),'refund', bixbyRequestHeader, bixbyRequestBody)


def authorizationReversal(authorisationGuid):
    bixbyReversalHeader, bixbyReversalBody = create_bixby_reversal('reversal', sharedSecret, cardAcceptor,authorisationGuid)
    return send_post_request('%s/web/%s/reversal' % (url, cardAcceptor),'reversal', bixbyReversalHeader, bixbyReversalBody)

def authorizationCancel(transactionType, terminalDateTime, currency, amount):
    bixbyCancellationHeader, bixbyCancellationBody = create_bixby_cancellation('cancellation', sharedSecret, cardAcceptor, transactionType, terminalDateTime, currency, amount)
    return send_post_request('%s/web/%s/cancellation' % (url, cardAcceptor), 'cancellation', bixbyCancellationHeader, bixbyCancellationBody)
