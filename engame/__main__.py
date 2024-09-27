import argparse
import logging
import requests
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import time
from sys import stdout
import csv
import os
#from dataclasses import dataclass

import math
from inspect import isfunction, isbuiltin
all_math_funcs = {n: f for (n, f) in vars(math).items() if isfunction(f) or isbuiltin(f)}

from .pairs import ng_pairs, bad_list
from .yq import YFQuote

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').strip().upper())
logging.getLogger('urllib3').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Quacks like a dict and an object
class QuotePair(dict):
    @property
    def src(self):
        return self.USD if self.src_cur == 'USD' else self.CAD
    @property
    def dst(self):
        return self.CAD if self.src_cur == 'USD' else self.USD

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(*e.args)
    def __setattr__(self, k, v):
        self[k]=v


def get_ng_data(src_cur: str, yfq: YFQuote):
    global ng_pairs
    j = {}
    for desc, usd, cad in ng_pairs:
        assert usd not in bad_list
        assert cad not in bad_list
        for currency, symbol in (('USD', usd), ('CAD', cad)):
            j[desc] = QuotePair(src_cur=src_cur,
                                USD=yfq.get_quote(desc, usd, 'USD'),
                                CAD=yfq.get_quote(desc, cad, 'CAD'))
    return j


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--verbose', action='count', default=0, help='Show long results with full calculations')
    p.add_argument('--max-lag', type=int, default=60, help='Maximum lag to accept (in seconds)')
    p.add_argument('src_cur', type=str.upper, choices=('USD', 'CAD'), help='Source currency (USD or CAD)')
    p.add_argument('src_amount', type=float, help='Amount of source currency to convert')
    g = p.add_argument_group('Commissions', '''
        These may be either fixed strings, or Python expressions using the variables `src_ask`, `dst_bid`, `shares`, `src_amount_convert`, and `dst_amount`,
        as well as any functions from `math` (e.g. `floor`) or builtins (e.g. `max`).''')
    g.add_argument('-S', '--src-commission', type=str, default='6.95', help="Commission for purchasing source-currency security (default %(default)r)")
    g.add_argument('-D', '--dst-commission', type=str, default='6.95', help="Commission for selling destination-currency security (default %(default)r)")

    args = p.parse_args()

    src_amount = args.src_amount
    src_cur = args.src_cur
    dst_cur = 'CAD' if src_cur == 'USD' else 'USD'

    now = time.time()

    print(f"Finding optimal securities to convert {src_cur} {src_amount:,.02f} to {dst_cur} using Norbert's Gambit.")
    print(f'- Commission function for purchasing source-currency security:   {args.src_commission}')
    print(f'- Commission function for selling destination-currency security: {args.dst_commission}')

    yfq = YFQuote()
    j = get_ng_data(src_cur, yfq)
    mmex = yfq.get_quote('USD/CAD mid-market rate', 'CAD=X', 'CAD')
    mm_rate = mmex.last_price ** (+1 if src_cur == 'USD' else -1)
    mm_lag = now - mmex.timestamp
    if mm_lag > args.max_lag:
        p.error(f'Lag in London mid-market exchange rate is too high ({mm_lag:.0f} sec)')
    print(f'\nLondon mid-market exchange rate for {src_cur} -> {dst_cur} is {mm_rate:,.04f} (LAG: {mm_lag:.0f} sec)\n')

    # Build table of results
    for desc, jd in j.items():
        src_symbol = jd.src.symbol
        dst_symbol = jd.dst.symbol
        src_ask = jd.src.ask
        dst_bid = jd.dst.bid

        shares, src_leftover = divmod(src_amount, src_ask)
        assert (shares := int(shares))
        src_amount_convert = src_amount - src_leftover
        dst_amount = shares * dst_bid

        commission_vars = dict(all_math_funcs, src_ask=src_ask, dst_bid=dst_bid, shares=shares, src_amount_convert=src_amount_convert, dst_amount=dst_amount)
        jd['src_commission'] = src_commission = eval(args.src_commission, commission_vars)
        jd['dst_commission'] = dst_commission = eval(args.dst_commission, commission_vars)

        src_amount_net = src_amount_convert + src_commission
        dst_amount_net = dst_amount - dst_commission

        jd['effective_rate'] = dst_amount_net / src_amount_net
        jd['theoretical_rate'] = dst_bid / src_ask
        jd['src_lag'] = now - jd[src_cur].timestamp
        jd['dst_lag'] = now - jd[dst_cur].timestamp

    # Display results
    print('Best options:\n')
    for ii, (desc, jd) in enumerate(
        sorted(((desc, jd) for (desc, jd) in j.items() if jd['src_lag'] <= args.max_lag and jd['dst_lag'] <= args.max_lag),
               key=lambda x: x[1]['effective_rate'], reverse=True)
    ):
        src_commission = jd['src_commission']
        dst_commission = jd['dst_commission']
        src_symbol = jd.src.symbol
        dst_symbol = jd.src.symbol
        src_ask = jd.src.ask
        dst_bid = jd.dst.bid
        src_lag = jd['src_lag']
        dst_lag = jd['dst_lag']
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

        if args.verbose < 2:
            print(f'{ii+1:-2d}. Buy {shares} x {src_symbol} at {src_cur} {src_ask:,.03f}, sell {dst_symbol} at {dst_cur} {dst_bid:,.03f}\n'
                  f'    Effective rate of {effective_rate:.04f}, losing {dst_cur} {loss_compared_to_mm:,.04f}')
            if args.verbose > 0:
                  print(f'    Commissions: {src_cur} {src_commission} (buy) and {dst_cur} {dst_commission} (sell)\n'
                        f'    LAG: {max(src_lag, dst_lag):.0f} sec')
        else:
            if ii > 0: print('\n==========================\n')
            print(f'Converting {src_cur} {src_amount:,.02f} to {dst_cur} using {desc} (CAD {jd["CAD"].symbol}, USD {jd["USD"].symbol})\n'
                f'\n'
                f'1. Buy {shares} shares of {src_symbol} in {src_cur} at ask of {src_ask:,.03f}, plus {src_commission:,.02f} commission\n'
                f'   (= {shares} x {src_ask:,.03f} + {src_commission:,.02f} = {src_amount_net:,.02f})\n'
                f'2. Sell {shares} shares of {dst_symbol} in {dst_cur} at bid of {dst_bid:,.03f}, less {dst_commission:,.02f} commission\n'
                f'   (= {shares} x {dst_bid:,.03f} - {dst_commission:,.02f} = {dst_amount_net:,.02f})\n'
                f'\n'
                f'You start with:   {src_cur} {src_amount_net:,.02f}\n'
                f'You end with:     {dst_cur} {dst_amount_net:,.02f}\n'
                f'               (+ {src_cur} {src_leftover:,.02f} leftover)\n'
                f'\n'
                f'Your effective conversion rate: {effective_rate:.04f}\n'
                f'Mid-market conversion rate:     {mm_rate:.04f}\n'
                f'Compared to MM rate, you lose:  {dst_cur} {loss_compared_to_mm:,.04f}')

if __name__ == '__main__':
    main()

    #print(dst_bid_over_src_ask)
    #print(eff_rate)
    #print(f'{src_cur} {src_amount} -> {dst_cur} {dst_amount_net}')

    #for currency, jc in jd.items():
        #wr.writerow((jc['symbol'], desc, jc['bid_size'], jc['bid'], jc['ask'], jc['ask_size'], jc['last_price'], jc['change'], jc['change_percent'], now - jc['timestamp']))

# with open('/tmp/foo.json', 'w') as outf:
#    json.dump(j, outf)
