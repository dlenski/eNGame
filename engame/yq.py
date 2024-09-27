from datetime import timezone, timedelta, time
import logging
from urllib.parse import quote_plus
from typing import Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class YFQuoteResult:
    symbol: str
    currency: str
    timestamp: int
    tz: timezone
    bid_size: Optional[int]
    ask_size: Optional[int]
    bid: Optional[float]
    ask: Optional[float]
    low: Optional[float]
    high: Optional[float]
    last_price: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]


def nav(r, *path, types_ok=(float, int), converter=None, ignore=(), expl='r'):
    for key in path:
        if not isinstance(r, dict):
            logger.warning(f'{expl} is unexpectedly of type {type(r)} rather than dict, returning None')
            return None
        elif key not in r:
            logger.warning(f'{expl} unexpectedly lacks key {key!r}, returning None')
            return None
        r = r[key]
        expl += f'[{key!r}]'
    if not(isinstance(r, types_ok)):
        logger.warning(f'{expl} is unexpectedly of type {type(r)} rather than {" OR ".join(types_ok)}, returning None')
        return None
    elif r in ignore:
        logger.warning(f'{expl} has value {r} which we ignore, returning None')
        return None

    return converter(r) if converter else r


class YFQuote:
    def __init__(self, sess: Optional[requests.Session]=None, crumb: Optional[str]=None, cookies: Optional[dict]=None):
        if sess is None:
            sess = requests.session()
            sess.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                #'Accept-Encoding': 'gzip, deflate',
                #'Accept-Language': 'en-US,en;q=0.5',
                #'Connection': 'keep-alive',
                #'Cache-Control': 'max-age=0',
            })

        if crumb is None or cookies is None:
            r = sess.get('https://query1.finance.yahoo.com/v1/test/getcrumb')
            r.raise_for_status()
            crumb = r.text
            logger.info(f"Got Yahoo Finance crumb {crumb!r} and cookies {','.join(c.name for c in sess.cookies if ('.'+c.domain).endswith('.yahoo.com'))}")

        self.sess = sess
        self.crumb = crumb

    def get_quote(self, desc, symbol, currency):
        r = self.sess.get(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?formatted=false&'
                    'modules=quoteType,summaryDetail,price'
                    # More available: ',summaryProfile,financialData,recommendationTrend,earnings,equityPerformance,defaultKeyStatistics,calendarEvents,esgScores,pageViews,financialsTemplate'
                    f'&lang=en-US&region=US&crumb={quote_plus(self.crumb)}')
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

        q = YFQuoteResult(
            symbol = symbol, tz = tz, currency = currency,
            timestamp = nav(res, 'price', 'regularMarketTime', expl=expl), # isoformat, converter=lambda ts: datetime.fromtimestamp(ts, tz), expl=expl).isoformat(),
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
        )
        logger.info(f'Got {jdesc}.')
        return q
