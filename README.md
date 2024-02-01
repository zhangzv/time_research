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
