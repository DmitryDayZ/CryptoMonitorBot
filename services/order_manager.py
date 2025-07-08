import logging
from exchanges.ccxt_client import ExchangeManager

ex_manager = ExchangeManager()

class OrderManager:
    def __init__(self):
        self.exchanges = ex_manager.exchanges  # словарь ccxt-инстансов по биржам

    async def buy_market(self, exchange_name: str, symbol: str, amount: float):
        """Купить на бирже market ордером."""
        try:
            order = await self.exchanges[exchange_name].create_market_buy_order(symbol, amount)
            logging.info(f"Market BUY ордер создан: {exchange_name} {symbol} {amount}")
            return order
        except Exception as e:
            logging.error(f"Ошибка создания market BUY ордера: {e}")
            return None

    async def buy_limit(self, exchange_name: str, symbol: str, amount: float, price: float):
        """Купить на бирже limit ордером."""
        try:
            order = await self.exchanges[exchange_name].create_limit_buy_order(symbol, amount, price)
            logging.info(f"Limit BUY ордер создан: {exchange_name} {symbol} {amount}@{price}")
            return order
        except Exception as e:
            logging.error(f"Ошибка создания limit BUY ордера: {e}")
            return None

    async def emulate_buy(self, exchange_name: str, symbol: str, amount: float, price: float = None):
        """Эмулировать покупку (без реального ордера)."""
        # logging.info(f"[Эмуляция] Покупка: {exchange_name} {symbol} {amount} по цене {price}")
        return {
            "exchange": exchange_name,
            "symbol": symbol,
            "side": "buy",
            "amount": amount,
            "price": price,
            "status": "emulated"
        }

    async def emulate_sell(self, exchange_name: str, symbol: str, amount: float, price: float = None):
        """Эмулировать продажу (без реального ордера)."""
        # logging.info(f"[Эмуляция] Продажа: {exchange_name} {symbol} {amount} по цене {price}")
        return {
            "exchange": exchange_name,
            "symbol": symbol,
            "side": "sell",
            "amount": amount,
            "price": price,
            "status": "emulated"
        }