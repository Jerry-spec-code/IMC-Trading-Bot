# IMC Trading Bot
A Python trading algorithm built for the IMC Prosperity challenge to trade different commodities based on their bid and ask prices using market making, correlation trading, and etf trading strategies

### Screenshots of Sample Results
<img width="494" alt="image" src="https://user-images.githubusercontent.com/78711575/229599356-d97f7c10-49f2-432b-8c7a-c581f695c11b.png">

### Project Setup 

Perform the following steps from the root directory

```sh
cd ./stockfish
python3 -m venv venv (Set up the virtual environment)
. venv/bin/activate  (Activate the virtual environment)
pip3 install -r requirements.txt (Install the required packages)
```
### Running the backtester

```sh
python3 bash.py {algorithm_file} && python3 backtester.py {round_number} {day_number}
```

Example:

```sh
python3 bash.py algorithms/round5.py && python3 backtester.py 4 3
```
