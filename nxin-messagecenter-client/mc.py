# -*- coding:utf-8 -*-
import sys
import time
import hashlib
import requests
from lxml import etree
from lxml.builder import E


domain = "XXX.nxin.com"
secret = "xxxxx"
sys_id = ""


def gen_xml(message, phones):
    if not isinstance(message, unicode):
        raise TypeError("%s must decode as unicode" % message)
    return etree.tostring(
        E("ShortMessage",
          E("sendSort", "SMS"),
          E("sendType", "COMMON_GROUP"),
          E("isGroup", "1"),
          E("phoneNumber", phones),
          E("isSwitchChannelRetry", "1"),
          E("message", message),
          E("remarks", sys_id)), encoding="utf-8")


def send_sms(message, phones, debug=False):
    api = "http://{0}/message/sendsmsCommonNxin".format(domain)
    timestamp = int(round(time.time() * 1000))
    token = hashlib.md5(secret + str(timestamp)).hexdigest()
    xml = gen_xml(message, phones)
    query = {"message": xml, "timestamp": timestamp, "systemId": sys_id, "accessToken": token}

    if debug:
        s = requests.Session()
        req = requests.Request('POST', api, params=query)
        prepped = req.prepare()
        print("url: %s" % prepped.path_url)
        resp = s.send(prepped)
    else:
        resp = requests.post(api, params=query)
    return resp


def test():
    response = send_sms("python testing 短信".decode('utf-8'), "138******")
    print(response.status_code, response.text)


if __name__ == '__main__':
    message = sys.argv[1].decode(sys.stdin.encoding)
    phone = sys.argv[2]
    resp = send_sms(message, phone)
    sys.stdout.write(resp.text.encode(sys.stdout.encoding))
