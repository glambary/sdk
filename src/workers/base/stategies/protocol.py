from typing import Any, Protocol


class ScheduleStrategyProtocol(Protocol):
    def next_delay(self, result: Any | None = None) -> float:
        pass
