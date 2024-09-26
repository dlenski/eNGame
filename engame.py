import logging
import requests
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import time
from sys import stdout
import csv
import os

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').strip().upper())
logging.getLogger('urllib3').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ng_pairs = (
                                          # US$ symbol    CA$ symbol
    ('Horizons U.S. Dollar Currency ETF', 'DLR-U.TO',    'DLR.TO'),
    ('TD (Canadian bank)',                'TD',          'TD.TO'),
    ('BMO (Canadian bank)',               'BMO',         'BMO.TO'),
    ('CIBC (Canadian bank)',              'CM',          'CM.TO'),
    ('ScotiaBank (Canadian bank)',        'BNS',         'BNS.TO'),
    ('RBC (Canadian bank)',               'RY',          'RY.TO'),
    ('Canadian National Railway',         'CNI',         'CNR.TO'),
    ('Enbridge (oil/energy)',             'ENB',         'ENB.TO'),
    ('Suncor (oil/energy)',               'SU',          'SU.TO'),
    ('MFC (insurance/investment)',        'MFC',         'MFC.TO'),
    ('Horizons S&P 500 ETF',              'HXS-U.TO',    'HXS.TO'),
    ('Horizons TSX60 ETF',                'HXT-U.TO',    'HXT.TO'),
    ('Horizons Global Dev Index ETF',     'HXDM-U.TO',   'HXDM.TO'),
    ('USD/CAD mid-market rate',           'CADUSD=X',    'USDCAD=X'),
)


def nav(r, *path, types_ok=(float, int), converter=None, ignore=(), expl='r'):
    for key in path:
        if not isinstance(r, dict):
            logging.warning(f'{expl} is unexpectedly of type {type(r)} rather than dict, returning None')
            return None
        elif key not in r:
            logging.warning(f'{expl} unexpectedly lacks key {key!r}, returning None')
            return None
        r = r[key]
        expl += f'[{key!r}]'
    if not(isinstance(r, types_ok)):
        logging.warning(f'{expl} is unexpectedly of type {type(r)} rather than {" OR ".join(types_ok)}, returning None')
        return None
    elif r in ignore:
        logging.warning(f'{expl} has value {r} which we ignore, returning None')
        return None

    return converter(r) if converter else r


def get_ng_data(sess=None, crumb=None):
    global ng_pairs

    if sess is None:
        sess = requests.session()
    if crumb is None:
        # https://stackoverflow.com/a/76320367
        r = sess.get('https://query1.finance.yahoo.com/v1/test/getcrumb')
        r.raise_for_status()
        crumb = r.text
        logger.info(f"Got Yahoo Finance crumb: {crumb!r}")

    j = {}
    for desc, usd, cad in ng_pairs:
        j[desc] = {}
        for currency, symbol in (('USD', usd), ('CAD', cad)):

            r = sess.get(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?formatted=false&'
                        'modules=quoteType,summaryDetail,price'
                        # More available: ',summaryProfile,financialData,recommendationTrend,earnings,equityPerformance,defaultKeyStatistics,calendarEvents,esgScores,pageViews,financialsTemplate'
                        f'&lang=en-US&region=US&crumb={urllib.parse.quote_plus(crumb)}')
            r.raise_for_status()

            jsym = r.json()
            jdesc = f'JSON for symbol {symbol} ({currency} side of {desc} pair)'
            if (err := jsym.get('error')) is not None:
                raise RuntimeError(f'Got error {err!r} for {jdesc}')
            if (qs := jsym.get('quoteSummary')) is None:
                raise AssertionError(f'No quoteSummary in {jdesc}')
            if len(res := qs.get('result', ())) != 1:
                raise AssertionError(f'quoteSummary.result has length {len(res)} rather than expected 1 in {jdesc}')

            res, = res
            expl = jdesc + ': quoteSummary.result[0]'

            assert (c := nav(res, 'summaryDetail', 'currency', types_ok=str)) == currency, \
                f'quoteSummary.result[0].summaryDetail.currency is {c!r} rather than expected {currency!r} in {jdesc}'
            # FIXME: USDCAD=X has a symbol of CAD=X here in the JSON...?
            assert (s := nav(res, 'quoteType', 'symbol', types_ok=str)) == symbol or (symbol == 'USDCAD=X' and s == 'CAD=X'), \
            f'quoteSummary.result[0].quoteType.symbol is {s!r} rather than expected {symbol!r} in {jdesc}'

            tzoffset = nav(res, 'quoteType', 'gmtOffSetMilliseconds')
            tzname = nav(res, 'quoteType', 'timeZoneFullName', types_ok=str)
            assert tzoffset is not None and tzname is not None
            tz = timezone(timedelta(seconds=tzoffset / 1000), tzname)

            d = dict(
                symbol = symbol,
                # FIXME: why are bid/ask size always zero for TSX symbols? https://www.reddit.com/r/YAHOOFINANCE/comments/1fahk77
                bid_size = nav(res, 'summaryDetail', 'bidSize', expl=expl, ignore=(0,)),
                ask_size = nav(res, 'summaryDetail', 'askSize', expl=expl, ignore=(0,)),
                bid = nav(res, 'summaryDetail', 'bid', expl=expl),
                ask = nav(res, 'summaryDetail', 'ask', expl=expl),
                low = nav(res, 'price', 'regularMarketDayLow', expl=expl),
                high = nav(res, 'price', 'regularMarketDayHigh', expl=expl),
                last_price = nav(res, 'price', 'regularMarketPrice', expl=expl),
                change = nav(res, 'price', 'regularMarketChange', expl=expl),
                change_percent = nav(res, 'price', 'regularMarketChangePercent', expl=expl),
                timestamp = nav(res, 'price', 'regularMarketTime', expl=expl) # isoformat, converter=lambda ts: datetime.fromtimestamp(ts, tz), expl=expl).isoformat(),
            )

            j[desc][currency] = d
            logging.info(f'Got {jdesc}.')

    return j


sess = requests.session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #'Accept-Encoding': 'gzip, deflate',
    #'Accept-Language': 'en-US,en;q=0.5',
    #'Connection': 'keep-alive',
    #'Cache-Control': 'max-age=0',
})


j = get_ng_data(sess)
wr = csv.writer(stdout, csv.excel_tab)
now = time.time()
for desc, jd in j.items():
    for currency, jc in jd.items():
        wr.writerow((jc['symbol'], desc, jc['bid_size'], jc['bid'], jc['ask'], jc['ask_size'], jc['last_price'], jc['change'], jc['change_percent'], now - jc['timestamp']))

# with open('/tmp/foo.json', 'w') as outf:
#    json.dump(j, outf)
