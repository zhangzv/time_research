# time_research

## Repo Introduction
- config
    - yaml file
- custom
    - .py file defining the signal
- output
    - logs
        - .log files, storing the logger information
    - missing
        - .csv files, storing the missing data points detected
    - report
        - .pdf files, showing the backtesting result
- utils
    - .py files, util functions
- main.py, the main script of the repo

If you want to run the script, please
    - install packages in requirements.txt
    - update the config file name in main.py if needed
    - run main.py
After you run, you will see folders under 'output' folder, where you can see the report


## Strategies
strat_v1.yml is the example signal that I submitted last time
strat_v2.yml is another signal with extra logic than the example:
    - introduced extra bybit information to define mid price
    - By oberserving the intermediate data, added extra logic to reduce the noise.
strat_v3.yml
    - improved the strat_v2 by setting dynamic boundary to define the abnormal event.
    - The trades are distributed more evenly across time.
    - has smaller drawdown.


## Ideas
The main concern of this strategy is transaction fees.
If the transaction fee is lower, then we will have much more opportunities to develop signals.

To ease the effect of transaction fee, I chose to reduce the trading frequency to 30m.
Because the price changes of 30m interval may potentially cover the transaction fee.
If the frequency is too high while transaction fee is not low enough,
then the price change if not able to cover the fee, which gives us loss all the time.

In this assignment, the signal is actually a pair trading strategy,
where by nature the same symbol in different exchange are highly correlated.

To further improve this signal, we can do:
    - introduce more data source to define a more accurate mid price
    - use other methods to define abnormal events and see the performance, bollinger band for example
    - extend to other pairs, which doesn't have to be the same symbol. Can be any symbols with high correlation,
        which is common in crypto.

Other signals I wanted to test:
    - When I looked at the data from binance and okx, I noticed their trading volume is very different.
    This is a good signal if we can bring liquidity from binance to okx by placing maker order in okx,
    which normally has higher spread in the orderbook. Using binance order book data, we can plus our
    profit margin to place order in okx. Once this maker order is filled, we can then place taker order
    in binance to hedge the position.
    Ideally this strategy only if the transaction fee is low enough and I think this strategy may work better
    in smaller coins with less attention. Big coins like BTC are too competitive that if our transaction fee
    is not low enough, the spread is normally not able to cover the transaction fee.


