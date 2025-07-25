import logging
import time

class VolumeSpikeStrategy:
    def __init__(self, spike_percent: float):
        self.spike_percent = spike_percent
        self.last_volume = {}

    async def check(self, exchange, symbol, old, current, volume):
        key = f"{exchange}_{symbol}"
        old_volume = self.last_volume.get(key)
        alerts = []

        if old_volume and old_volume != 0:
            diff = abs(volume - old_volume) / old_volume * 100
            logging.info(f"InitialThresholdStrategy: изменение {diff:.2f}% для {exchange} {symbol}")
            if diff >= self.spike_percent:
                direction = "📈 Резкий рост объёма" if volume > old_volume else "📉 Резкое падение объёма"
                alerts.append({
                    "exchange": exchange,
                    "symbol": symbol,
                    "old": old_volume,
                    "new": volume,
                    "diff": diff,
                    "direction": direction,
                    "strategy": f"VolumeSpikeStrategy ({self.spike_percent}%)",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
        self.last_volume[key] = volume
        return alerts