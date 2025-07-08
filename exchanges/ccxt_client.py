
import ccxt.async_support as ccxt

class ExchangeManager:
    def __init__(self):
        self.exchanges = {
            "binance": ccxt.binance(),
            "bybit": ccxt.bybit(),
        }

    async def fetch_price(self, exchange_name: str, symbol: str) -> float:
        ex = self.exchanges[exchange_name]
        ticker = await ex.fetch_ticker(symbol)
        return ticker['last']

    async def close_all(self):
        # Закрыть соединения с биржами
        for ex in self.exchanges.values():
            await ex.close()