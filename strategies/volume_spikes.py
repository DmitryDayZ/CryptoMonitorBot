class VolumeSpikeStrategy:
    def __init__(self, spike_percent: float):
        self.spike_percent = spike_percent
        self.last_volume = {}

    async def check(self, exchange, symbol, old, current, volume):
        key = f"{exchange}_{symbol}"
        old_volume = self.last_volume.get(key)
        alerts = []
        if old_volume and abs(volume - old_volume) / old_volume * 100 >= self.spike_percent:
            direction = "📈 Резкий рост объёма" if volume > old_volume else "📉 Резкое падение объёма"
            alerts.append({
                "exchange": exchange,
                "pair": symbol,
                "old_volume": old_volume,
                "new_volume": volume,
                "direction": direction
            })
        self.last_volume[key] = volume
        return alerts