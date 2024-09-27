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


def get_yf_quote(desc, symbol, currency, sess, crumb):
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
    logging.info(f'Got {jdesc}.')
    return d


def get_ng_data(sess, crumb):
    global ng_pairs
    j = {}
    for desc, usd, cad in ng_pairs:
        j[desc] = {}
        for currency, symbol in (('USD', usd), ('CAD', cad)):
            j[desc][currency] = get_yf_quote(desc, symbol, currency, sess, crumb)

    return j


############################


sess = requests.session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #'Accept-Encoding': 'gzip, deflate',
    #'Accept-Language': 'en-US,en;q=0.5',
    #'Connection': 'keep-alive',
    #'Cache-Control': 'max-age=0',
})

# Get required "crumb" (https://stackoverflow.com/a/76320367)
r = sess.get('https://query1.finance.yahoo.com/v1/test/getcrumb')
r.raise_for_status()
crumb = r.text
logger.info(f"Got Yahoo Finance crumb: {crumb!r}")

src_amount = 10_000.0
src_cur = 'USD'
dst_cur = 'CAD' if src_cur == 'USD' else 'USD'

j = get_ng_data(sess, crumb)
mmex = get_yf_quote('USD/CAD mid-market rate', 'CAD=X', 'CAD', sess, crumb)
mm_rate = mmex["last_price"] ** (+1 if src_cur == 'USD' else -1)

#wr = csv.writer(stdout, csv.excel_tab)
now = time.time()
for desc, jd in j.items():
    src_commission = dst_commission = 6.95  # FIXME customizable commission function?
    src_symbol = jd[src_cur]['symbol']
    dst_symbol = jd[dst_cur]['symbol']
    src_ask = jd[src_cur]['ask']
    dst_bid = jd[dst_cur]['bid']

    shares, src_leftover = divmod(src_amount, src_ask)
    assert (shares := int(shares))
    src_amount_convert = src_amount - src_leftover
    src_amount_net = src_amount_convert + src_commission
    dst_amount = shares * dst_bid
    dst_amount_net = dst_amount - dst_commission

    jd['src_commission'] = src_commission
    jd['dst_commission'] = dst_commission
    jd['effective_rate'] = dst_amount_net / src_amount_net
    jd['theoretical_rate'] = dst_bid / src_ask

first = True
for desc, jd in sorted(j.items(), key=lambda x: x[1]['effective_rate']):
    src_commission = jd['src_commission']
    dst_commission = jd['dst_commission']
    src_symbol = jd[src_cur]['symbol']
    dst_symbol = jd[dst_cur]['symbol']
    src_ask = jd[src_cur]['ask']
    dst_bid = jd[dst_cur]['bid']
    theoretical_rate = jd['theoretical_rate']
    effective_rate = jd['effective_rate']

    shares, src_leftover = divmod(src_amount, src_ask)
    assert (shares := int(shares))
    src_amount_convert = src_amount - src_leftover
    src_amount_net = src_amount_convert + src_commission
    dst_amount = shares * dst_bid
    dst_amount_net = dst_amount - dst_commission

    dst_amount_mm = src_amount_net * mm_rate
    loss_compared_to_mm = dst_amount_mm - dst_amount_net

    if first: first = False
    else: print('\n==========================\n')

    print(f'Converting {src_cur} {src_amount:,.02f} to {dst_cur} using {desc} (CAD {jd["USD"]["symbol"]}, USD {jd["USD"]["symbol"]})\n'
          f'\n'
          f'1. Buy {shares} shares of {src_symbol} in {src_cur} at ask of {src_ask:,.03f}, plus {src_commission:,.02f} commission\n'
          f'   (= {shares} x {src_ask:,.03f} + {src_commission:,.02f} = {src_amount_net:,.02f})\n'
          f'2. Sell {shares} shares of {dst_symbol} in {dst_cur} at bid of {dst_bid:,.03f}, less {dst_commission:,.02f} commission\n'
          f'   (= {shares} x {dst_bid:,.03f} - {dst_commission:,.02f} = {dst_amount_net:,.02f})\n'
          f'\n'
          f'You spend:   {src_cur} {src_amount_net:,.02f}\n'
          f'          (+ {src_cur} {src_leftover:,.02f} leftover)\n'
          f'You receive: {dst_cur} {dst_amount_net:,.02f}\n'
          f'\n'
          f'Your effective conversion rate: {effective_rate:.04f}\n'
          f'Mid-market conversion rate:     {mm_rate:.04f}\n'
          f'Compared to MM rate, you lose:  {dst_cur} {loss_compared_to_mm:,.04f}')

    #print(dst_bid_over_src_ask)
    #print(eff_rate)
    #print(f'{src_cur} {src_amount} -> {dst_cur} {dst_amount_net}')

    #for currency, jc in jd.items():
        #wr.writerow((jc['symbol'], desc, jc['bid_size'], jc['bid'], jc['ask'], jc['ask_size'], jc['last_price'], jc['change'], jc['change_percent'], now - jc['timestamp']))

# with open('/tmp/foo.json', 'w') as outf:
#    json.dump(j, outf)
