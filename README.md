# eNGame

A tool to help you pick the optimal securities to convert between US and Canadian currency using Norbert's Gambit,
based on near-realtime data obtained from Yahoo Finance.

- Forum thread: https://www.financialwisdomforum.org/forum/viewtopic.php?t=198
- Wiki explainer: https://www.finiki.org/wiki/Norbert%27s_gambit
- Forbes article: https://www.forbes.com/advisor/ca/investing/what-is-norberts-gambit/

# Example

My brokerage charges me commissions of US\$15.00 + US\$0.01/share to buy US\$ securities,
and a flat CA\$8.00 to sell CA\$ securities.

I can execute both of the trades near-instantaneously, [without
needing to call or message my broker to "journal" shares from one currency to the other](https://www.finiki.org/wiki/Norbert%27s_gambit#An_example:~:text=you%20usually%20must%20request%20that%20the%20broker%20journal%20shares%20from%20the%20long%20side%20to%20cover%20the%20short%20on%20settlement%20date%20two%20business%20days%20(T%20%2B%202)%20later.%20This%20usually%20requires%20a%20phone%20call%20to%20the%20broker.) BMO InvestorLine
is an example of a brokerage where [no journaling step is required](https://www.reddit.com/r/PersonalFinanceCanada/comments/ya3bwh.

I want to convert US\$50,000 to CA\$. Right now, the mid-market exchange rate is about 1.3512 CAD/USD.

What are the 5 best
[interlisted CA\$/US\$ stocks or ETFs](https://www.canadianmoneyforum.com/threads/dual-listed-etfs-tsx-nyse.135364/post-1972456)
to use to do this conversion right now?

Engame can show you the best options. Note that the three best options right now would get you an effective exchange rate
that's _actually slightly better than_ the mid-market exchange rate, _assuming that you execute both sides of the trade near-instantaneously
at the stated bid/ask prices_:

```
$ engame USD 50000 -v -L 5 -S '15.00 + 0.01 * shares' -D '8.00'
```
![Screenshot](screenshot.png)

# Details

Run `engame --help` for more details.

# TODO

Configuration file for preferred symbols and commission structure?

Automatic detection of some of the common [pitfalls and problems](https://www.finiki.org/wiki/Norbert%27s_gambit#Pitfalls_and_problems),
including ex-dividend dates and differing market holidays on US and Canadian markets.

# Disclaimers

1. Do not use this if you don't understand how Norbert's Gambit works.
2. I take no responsibility for the accuracy or the timeliness of the stock/ETF/currency data.
3. I take no responsibility for the correctness of the calculations.
4. Without a realtime data source for [Level II quotes](https://www.investopedia.com/articles/trading/06/level2quotes.asp#toc-what-is-level-ii),
   we cannot be sure that there is sufficient market depth to complete both sides of the trade at the expected prices. Limit orders
   cannot protect you here, because _both sides_ of the trade need to complete quickly in order to achieve the desired
   currency-conversion outcome.
