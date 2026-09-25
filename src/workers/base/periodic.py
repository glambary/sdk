import asyncio
import logging

from workers.base.base import BaseWorker
from workers.base.stategies.protocol import ScheduleStrategyProtocol

logger = logging.getLogger(__name__)


class BasePeriodicWorker(BaseWorker):
    _strategy: ScheduleStrategyProtocol

    async def _run_loop(self) -> None:
        result: float | None = None

        while not self._on_stopped.is_set():
            sleep_delay = self._strategy.next_delay(result=result)

            logger.info("Sleeping delay %.2f", sleep_delay)

            try:
                await asyncio.wait_for(
                    self._on_stopped.wait(),
                    timeout=sleep_delay,
                )
            except TimeoutError:
                pass

            if self._on_stopped.is_set():
                break

            result = await self.process()

    async def process(self) -> float | None:
        raise NotImplementedError
