class CronScheduleStrategy:
    """
    Крон стратегия.

    Example:
    Каждый день в 6 утра по UTC.

    # минуты час день_месяца месяц день_недели
    CronScheduleStrategy("0 6 * * *")
    """

    def __init__(self, cron_expr: str, start_time: datetime | None = None) -> None:
        logger.info(f"CronScheduleStrategy: {cron_expr}")

        start_time = start_time or datetime.now(tz=UTC)

        self._cron_expr = cron_expr
        self._croniter = croniter(expr_format=cron_expr, start_time=start_time)

    def next_delay(self, *_: tuple[Any, ...], **__: dict[str, Any]) -> float:
        next_run = self._croniter.get_next(datetime)
        delay = (next_run - datetime.now(tz=UTC)).total_seconds()

        return max(0, delay)
