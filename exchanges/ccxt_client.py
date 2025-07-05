import ccxt

class ExchangeManager:
    def __init__(self):
        self.exchanges = {
            "binance": ccxt.binance(),
            "bybit": ccxt.bybit(),
        }

    def fetch_price(self, exchange_name: str, symbol: str) -> float:
        ex = self.exchanges[exchange_name]
        ticker = ex.fetch_ticker(symbol)
        return ticker['last']
