'''
Pairs of interlisted USD/CAD stocks and ETFs for Norbert's Gambit

Mostly taken from "Best stocks for Norbert's Gambit" thread:
https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456

US CUSIP search: https://www.quantumonline.com/search.cfm?sopt=symbol&tickersymbol=AAA
'''

from collections import namedtuple
p = namedtuple('SameCusipPair', ('desc', 'cusip', 'usd', 'cad', 'wssecid'))

ng_pairs = (
    #                                                      |---- Yahoo Finance ----|    |------------- WealthSimple ------------|
    #                                        CUSIP         US$ symbol     CA$ symbol    CA$ security ID
    p('Horizons U.S. Dollar Currency ETF',   '379948102',  'DLR-U.TO',    'DLR.TO',     'sec-s-4c836ded25404e71862ac52ff5219506'),
    p('TD (Canadian bank)',                  '891160509',  'TD',          'TD.TO',      'sec-s-ea5e995e98774e3d998aa5dae06cf237'),
    p('BMO (Canadian bank)',                 '063671101',  'BMO',         'BMO.TO',     'sec-s-d670c0c7745743f8a0f469b2f02444fc'),
    p('CIBC (Canadian bank)',                '136069101',  'CM',          'CM.TO',      'sec-s-b898f6623a2c42649f9e9b53532b073c'),
    p('ScotiaBank (Canadian bank)',          '064149107',  'BNS',         'BNS.TO',     'sec-s-cac48e23f5b84b4787b97628581ce59f'),
    p('RBC (Canadian bank)',                 '780087102',  'RY',          'RY.TO',      'sec-s-3305aeb61f3a4b8797140439b028689b'),
    p('Canadian National Railway',           '136375102',  'CNI',         'CNR.TO',     'sec-s-37f80b493095405189c7ea131adfd8ce'),
    p('Enbridge (oil/energy)',               '29250N105',  'ENB',         'ENB.TO',     'sec-s-5405e20fa09946d29c768e0d41a4195d'),
    p('Suncor (oil/energy)',                 '867224107',  'SU',          'SU.TO',      'sec-s-e90effe2699b47acbd69e96ffd0fea97'),
    p('MFC (insurance/investment)',          '56501R106',  'MFC',         'MFC.TO',     'sec-s-82d7214a0efa4d338bb8307838f8f0aa'),
    p('Horizons S&P 500 ETF',                '37964P100',  'HXS-U.TO',    'HXS.TO',     'sec-s-27165f620fe14413bd2ee518716fa53f'),
    p('Horizons TSX60 ETF',                  '37963M108',  'HXT-U.TO',    'HXT.TO',     'sec-s-12d0b80be5384550baf4b6a9ab21b7a2'),
    p('Horizons Global Dev Index ETF',       '37963V108',  'HXDM-U.TO',   'HXDM.TO',    'sec-s-bc584288e77b4d4994cbc9bffa0a8373'),
    p('Thompson Reuters',                    '884903709',  'TRI',         'TRI.TO',     'sec-s-8e618c90909b4908b75997d4a497d07a'),
)

# IT IS NOT POSSIBLE TO USE THESE PAIRS FOR NORBERT'S GAMBIT
# because the USD/CAD symbols do not share the same CUSIPs.
#
# Taken from https://www.finiki.org/wiki/Norbert%27s_gambit#ETFs_with_different_CUSIPs

bad_list = (
    'ZSP.U', 'ZSP',
    'XEF.U', 'XEF',
    'XUS.U', 'XUS',
    'XUU.U', 'XUU',
)
