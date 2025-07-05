
from typing import Protocol, Any, Dict, List

class Strategy(Protocol):
    async def check(self, exchange: str, symbol: str, old: float, current: float) -> List[Dict[str, Any]]:
        ...