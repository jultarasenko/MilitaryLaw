"""Background jobs module."""

from militarylaw_bot.jobs.daily_stats import send_daily_stats

__all__ = ["send_daily_stats"]
