import argparse
import logging
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import time
from sys import stdout
import csv
import os
from itertools import count
#from dataclasses import dataclass

import math
from inspect import isfunction, isbuiltin
all_math_funcs = {n: f for (n, f) in vars(math).items() if isfunction(f) or isbuiltin(f)}

import requests
from colored import Fore, Back, Style

from .pairs import ng_pairs, bad_list
from .yq import YFQuote

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'WARNING').strip().upper())
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
    p = argparse.ArgumentParser(description="A tool to help you pick the optimal securities to convert between US and Canadian currency using Norbert's Gambit, based on near-realtime quotes from Yahoo Finance.")
    p.add_argument('-v', '--verbose', action='count', default=0, help='Show long results with full calculations')
    p.add_argument('--max-lag', type=int, default=60, help='Maximum lag to accept (in seconds)')
    p.add_argument('-L', '--limit', type=int, default=math.inf, help='Only show the best LIMIT results')
    p.add_argument('src_cur', type=str.upper, choices=('USD', 'CAD'), help='Source currency (USD or CAD)')
    p.add_argument('src_amount', type=float, help='Amount of source currency to convert')
    g = p.add_argument_group('Commissions', '''
        These may be either fixed strings, or Python expressions using the variables `src_ask`, `dst_bid`, `shares`, `src_amount_convert`, and `dst_amount`,
        as well as any functions from `math` (e.g. `floor`) or builtins (e.g. `max`).''')
    g.add_argument('-S', '--src-commission', type=str, default='6.95', help="Commission for buying source-currency security (default %(default)r)")
    g.add_argument('-D', '--dst-commission', type=str, default='6.95', help="Commission for selling destination-currency security (default %(default)r)")

    args = p.parse_args()

    src_amount = args.src_amount
    src_cur = args.src_cur
    dst_cur = 'CAD' if src_cur == 'USD' else 'USD'

    now = time.time()

    yfq = YFQuote()
    j = get_ng_data(src_cur, yfq)
    mmex = yfq.get_quote('USD/CAD mid-market rate', 'CAD=X', 'CAD')
    mm_rate = mmex.last_price ** (+1 if src_cur == 'USD' else -1)
    mm_lag = now - mmex.timestamp
    if mm_lag > args.max_lag:
        p.error(f'Lag in London mid-market exchange rate is too high ({mm_lag:.0f} sec). Are US and Canadian markets open?')

    print(f"Finding optimal securities to convert {Fore.red}{src_cur} {src_amount:,.02f}{Style.reset} to {Fore.green}{dst_cur}{Style.reset} using Norbert's Gambit.")
    print(f'- Commission function for buying {src_cur} security:  {Fore.red}{args.src_commission}{Style.reset}')
    print(f'- Commission function for selling {dst_cur} security: {Fore.green}{args.dst_commission}{Style.reset}')
    print(f'\nLondon mid-market exchange rate for {Fore.red}{src_cur}{Style.reset} -> {Fore.green}{dst_cur}{Style.reset}'
          f' is {Fore.yellow}{mm_rate:,.04f}{Style.reset}'
          f' ({Style.bold}{mm_lag:.0f} sec lag{Style.reset})\n')

    # Calculate results and stash them in the dict of quotes
    for desc, jd in j.items():
        for reduce in count():
            # How many shares should we buy/sell?
            shares = jd['shares'] = src_amount // jd.src.ask - reduce
            src_amount_convert = src_amount_convert = shares * jd.src.ask
            dst_amount = shares * jd.dst.bid

            # Calculate commissions
            commission_vars = dict(all_math_funcs, src_ask=jd.src.ask, dst_bid=jd.dst.bid, shares=shares, src_amount_convert=src_amount_convert, dst_amount=dst_amount)
            src_commission = jd['src_commission'] = eval(args.src_commission, commission_vars)
            dst_commission = jd['dst_commission'] = eval(args.dst_commission, commission_vars)

            # Net amounts outgoing and incoming after commissions
            src_amount_net = jd['src_amount_net'] = src_amount_convert + src_commission
            src_leftover = jd['src_leftover'] = src_amount - src_amount_net
            dst_amount_net = jd['dst_amount_net'] = dst_amount - dst_commission

            # Keep reducing by one share until we're below the starting amount after commission
            if src_leftover >= 0.0:
                break

        # Stash results
        jd['effective_rate'] = dst_amount_net / src_amount_net
        jd['theoretical_rate'] = jd.dst.bid / jd.src.ask
        jd['src_lag'] = now - jd.src.timestamp
        jd['dst_lag'] = now - jd.dst.timestamp

    lag_ok = [(desc, jd) for (desc, jd) in j.items() if jd['src_lag'] <= args.max_lag and jd['dst_lag'] <= args.max_lag]
    if not lag_ok:
        p.error(f'Out of {len(j)} interlisted stocks/ETFs, none have lag of <={args.max_lag} sec. Are US and Canadian markets open?')
    lag_ok.sort(key=lambda x: x[1]['effective_rate'], reverse=True)
    print(f'Out of {len(j)} pairs of interlisted stocks/ETFs, {len(lag_ok)} have lag of <={args.max_lag} sec.')

    # Display results ranked from best to worst
    print('Best options:\n')
    for ii, (desc, jd) in enumerate(lag_ok):
        if ii >= args.limit:
            break

        shares = jd['shares']
        src_commission = jd['src_commission']
        dst_commission = jd['dst_commission']
        src_amount_net = jd['src_amount_net']
        src_leftover = jd['src_leftover']
        dst_amount_net = jd['dst_amount_net']
        effective_rate = jd['effective_rate']
        theoretical_rate = jd['theoretical_rate']
        src_lag = jd['src_lag']
        dst_lag = jd['dst_lag']

        dst_amount_mm = src_amount_net * mm_rate
        loss_compared_to_mm = dst_amount_mm - dst_amount_net

        if args.verbose < 2:
            print(f'{ii+1:-2d}. Buy {Style.bold}{shares:.0f}{Style.reset} x {Fore.red}{jd.src.symbol}{Style.reset} at {Fore.red}{src_cur} {jd.src.ask:,.03f}{Style.reset} ({Style.bold}{src_lag:.0f} sec lag{Style.reset}),'
                  f' sell {Fore.green}{jd.dst.symbol}{Style.reset} at {Fore.green}{dst_cur} {jd.dst.bid:,.03f}{Style.reset} ({Style.bold}{dst_lag:.0f} sec lag{Style.reset})\n'
                  f'    Effective rate of {Fore.yellow}{effective_rate:.04f}{Style.reset}\n'
                  f'    Losing {Fore.green}{dst_cur} {loss_compared_to_mm:,.04f}{Style.reset} compared to London mid-market')
            if args.verbose > 0:
                  print(f'    Net of commissions of {Fore.red}{src_cur} {src_commission:,.02f}{Style.reset} (buy) and {Fore.green}{dst_cur} {dst_commission:,.02f}{Style.reset} (sell)')
            print()

        else:
            print(f'{ii+1:-2d}. Using {desc}:       [ {Style.bold}{max(src_lag, dst_lag):.0f} sec data lag{Style.reset} ]\n\n'
                f'    a. Buy {Style.bold}{shares:.0f}{Style.reset} shares of {Fore.red}{jd.src.symbol}{Style.reset} at ask of {Fore.red}{src_cur} {jd.src.ask:,.03f}{Style.reset}, plus {Fore.red}{src_cur} {src_commission}{Style.reset} commission\n'
                f'       (= {shares:.0f} x {jd.src.ask:,.03f} + {src_commission:,.02f} = {src_amount_net:,.02f})\n'
                f'    b. Sell {Style.bold}{shares:.0f}{Style.reset} shares of {Fore.green}{jd.dst.symbol}{Style.reset} at bid of {Fore.green}{dst_cur} {jd.dst.bid:,.03f}{Style.reset}, less {Fore.green}{dst_cur} {dst_commission}{Style.reset} commission\n'
                f'       (= {shares:.0f} x {jd.dst.bid:,.03f} - {dst_commission:,.02f} = {dst_amount_net:,.02f})\n\n'
                f'    You end up with: {Fore.green}{dst_cur} {dst_amount_net:,.02f}{Style.reset} (+ leftover {Fore.red}{src_cur} {src_leftover:,.02f}{Style.reset})\n'
                f'    Your effective conversion rate: {Fore.yellow}{effective_rate:.04f}{Style.reset}\n'
                f'    Mid-market conversion rate:     {Fore.yellow}{mm_rate:.04f}{Style.reset}\n'
                f'    Compared to MM rate, you lose:  {Fore.green}{dst_cur} {loss_compared_to_mm:,.04f}{Style.reset}\n')

if __name__ == '__main__':
    main()

    #print(dst_bid_over_src_ask)
    #print(eff_rate)
    #print(f'{src_cur} {src_amount} -> {dst_cur} {dst_amount_net}')

    #for currency, jc in jd.items():
        #wr.writerow((jc['symbol'], desc, jc['bid_size'], jc['bid'], jc['ask'], jc['ask_size'], jc['last_price'], jc['change'], jc['change_percent'], now - jc['timestamp']))

# with open('/tmp/foo.json', 'w') as outf:
#    json.dump(j, outf)
