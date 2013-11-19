# coding=utf-8
import json
from pprint import pprint
import urllib2
import httplib


VERSIONS = {
    'live': 'https://api.direct.yandex.ru/live/v4/json/',
    'v4': 'https://api.direct.yandex.ru/v4/json/'
}


CURRENCY = ('RUB', 'CHF', 'EUR', 'KZT', 'TRY', 'UAH', 'USD')
KEYFILE = '/Users/andrey/projects/upink_modules/modules/reports_day_direction/private.key'
CERTFILE = '/Users/andrey/projects/upink_modules/modules/reports_day_direction/cert.crt'


class YandexCertConnection(httplib.HTTPSConnection):
    def __init__(self, host, port=None, key_file=KEYFILE, cert_file=CERTFILE, timeout=30):
        httplib.HTTPSConnection.__init__(self, host, port, key_file, cert_file)


class YandexCertHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(YandexCertConnection, req)
    https_request = urllib2.AbstractHTTPHandler.do_request_


class YandexDirect(object):

    def __init__(self, version='live'):
        self.version = version
        self.url = VERSIONS[version]
        self.urlopener = urllib2.build_opener(*[YandexCertHandler()])

    def request(self, method, params):
        if method:
            data = {
                "method": method,
                "param": params
            }
            response = self.urlopener.open(self.url, json.dumps(data, ensure_ascii=False).encode('utf8'))
            result = response.read().decode('utf8')
            return json.loads(result)['data']

    def get_clients_list(self, status_arch='No'):
        params = {
            "Filter": {
                "StatusArch": status_arch
            }
        }
        return self.request("GetClientsList", params)

    def get_summary_stat(self, campaign_ids, start_date, end_date, currency='', include_vat='No', include_discount='No'):
        params = {}
        if campaign_ids is not None:
            params["CampaignIDS"] = campaign_ids
        else:
            raise ValueError('campaign_ids required')
        if start_date:
            params["StartDate"] = start_date
        else:
            raise ValueError('start_date required')
        if end_date:
            params["EndDate"] = end_date
        else:
            raise ValueError('start_date required')

        params.update({
            #"Currency": currency,
            #"IncludeVAT": include_vat,
            #"IncludeDiscount": include_discount
        })
        return self.request("GetSummaryStat", params)


# company_id = 4483876


#urlopener = urllib2.build_opener(*[YandexCertHandler()])
#
#data = {
#    "method": "GetSummaryStat",
#    "param": {
#        'CampaignIDS': [4483876],
#        'StartDate': '2013-11-01',
#        'EndDate': '2013-11-16'
#    }
#}
#
##выполнить запрос
#response = urlopener.open('https://api.direct.yandex.ru/live/v4/json/', json.dumps(data, ensure_ascii=False).encode('utf8'))
#
##вывести результат
#result = response.read().decode('utf8')
#res = json.loads()
#
#r = '''{"data":
#[
#{"ClicksSearch":5,"SumSearch":10.33,"SessionDepthSearch":"3.33","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-01","ShowsSearch":78,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":6,"SumSearch":8.34,"SessionDepthSearch":"6.50","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-02","ShowsSearch":130,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":11,"SumSearch":16.55,"SessionDepthSearch":null,"SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":null,"SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-03","ShowsSearch":167,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":4,"SumSearch":7.49,"SessionDepthSearch":"3.50","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-04","ShowsSearch":74,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":4,"SumSearch":8.05,"SessionDepthSearch":"3.00","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-05","ShowsSearch":73,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":9,"SumSearch":9.08,"SessionDepthSearch":null,"SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":null,"SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-06","ShowsSearch":110,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":9,"SumSearch":11.77,"SessionDepthSearch":"2.50","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-07","ShowsSearch":172,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":6,"SumSearch":8.88,"SessionDepthSearch":"2.33","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-08","ShowsSearch":124,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":5,"SumSearch":7.41,"SessionDepthSearch":"4.00","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-09","ShowsSearch":110,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":9,"SumSearch":13.75,"SessionDepthSearch":"2.56","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-10","ShowsSearch":151,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":19,"SumSearch":31.53,"SessionDepthSearch":null,"SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":null,"SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-11","ShowsSearch":120,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":3,"SumSearch":3.52,"SessionDepthSearch":"2.00","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-12","ShowsSearch":62,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":12,"SumSearch":18.31,"SessionDepthSearch":"3.80","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-13","ShowsSearch":103,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":9,"SumSearch":14.45,"SessionDepthSearch":"3.12","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-14","ShowsSearch":161,"CampaignID":4483876,"ShowsContext":0},
#
#{"ClicksSearch":11,"SumSearch":18.35,"SessionDepthSearch":"3.00","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-15","ShowsSearch":149,"CampaignID":4483876,"ShowsContext":0},
#
#{"ClicksSearch":7,"SumSearch":13.21,"SessionDepthSearch":"2.14","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-16","ShowsSearch":98,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":6,"SumSearch":4.29,"SessionDepthSearch":"2.33","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-17","ShowsSearch":135,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":3,"SumSearch":4.82,"SessionDepthSearch":"2.50","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-18","ShowsSearch":68,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":3,"SumSearch":4.14,"SessionDepthSearch":"4.33","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-19","ShowsSearch":63,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":9,"SumSearch":12.6,"SessionDepthSearch":"3.67","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-20","ShowsSearch":110,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":11,"SumSearch":18.58,"SessionDepthSearch":"4.20","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-21","ShowsSearch":152,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":10,"SumSearch":17.12,"SessionDepthSearch":"3.80","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-22","ShowsSearch":155,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":10,"SumSearch":19.44,"SessionDepthSearch":"4.20","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-23","ShowsSearch":127,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":8,"SumSearch":9.53,"SessionDepthSearch":"2.00","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-24","ShowsSearch":159,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":11,"SumSearch":18.27,"SessionDepthSearch":"2.30","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-25","ShowsSearch":101,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":8,"SumSearch":11.98,"SessionDepthSearch":"2.67","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-26","ShowsSearch":73,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":12,"SumSearch":14.77,"SessionDepthSearch":"3.90","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-27","ShowsSearch":127,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":15,"SumSearch":20.56,"SessionDepthSearch":"2.14","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-28","ShowsSearch":131,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":7,"SumSearch":10.32,"SessionDepthSearch":"2.67","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-29","ShowsSearch":127,"CampaignID":4483876,"ShowsContext":0},
#{"ClicksSearch":7,"SumSearch":10.76,"SessionDepthSearch":"2.83","SessionDepthContext":null,"ClicksContext":0,"GoalCostContext":null,"GoalCostSearch":null,"GoalConversionSearch":"0.00","SumContext":0,"GoalConversionContext":null,"StatDate":"2013-10-30","ShowsSearch":122,"CampaignID":4483876,"ShowsContext":0}]}'''
##pprint(json.loads(r))
#for item in json.loads(r)['data']:
#    print item['CampaignID'], item['StatDate'], item['SumSearch']
